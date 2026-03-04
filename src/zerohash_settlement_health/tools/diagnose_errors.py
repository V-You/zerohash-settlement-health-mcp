"""diagnose_errors tool — parses API error logs and classifies incidents."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from zerohash_settlement_health.log_parser import (
    build_provider_impact,
    group_into_incidents,
    parse_log_lines,
)
from zerohash_settlement_health.models import ErrorResponse
from zerohash_settlement_health.models.incident import (
    DiagnosisResult,
    Incident,
    ProviderImpact,
    Summary,
)
from zerohash_settlement_health.runbooks import match_error_runbook


_ALLOWED_EXTENSIONS = {".log", ".txt"}


def _validate_file_path(file_path: str) -> Optional[dict]:
    """Validate file_path: relative only, no traversal, allowed extensions.

    Returns an ErrorResponse dict if invalid, None if valid.
    """
    if os.path.isabs(file_path):
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message="file_path must be a relative path to a .log or .txt file",
        ).model_dump()

    parts = Path(file_path).parts
    if ".." in parts:
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message="file_path must be a relative path to a .log or .txt file",
        ).model_dump()

    suffix = Path(file_path).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message="file_path must be a relative path to a .log or .txt file",
        ).model_dump()

    return None


def _classify_category(status_code: Optional[int], runbook: Optional[dict]) -> str:
    """Determine incident category from runbook or status code range."""
    if runbook:
        return runbook.get("category", "UNKNOWN")
    if status_code is not None:
        if 400 <= status_code < 500:
            return "CLIENT_SIDE"
        if 500 <= status_code < 600:
            return "SERVER_SIDE"
    return "UNKNOWN"


def _fill_template(
    template: str,
    client_id: Optional[str],
    timestamp: str,
    endpoint: Optional[str],
) -> str:
    """Fill draft_response_template placeholders."""
    return template.format(
        client_id=client_id or "Client",
        timestamp=timestamp,
        endpoint=endpoint or "request",
    ).strip()


def diagnose_errors(
    log_text: Optional[str] = None,
    file_path: Optional[str] = None,
) -> dict:
    """Parse API error logs and diagnose incidents.

    Args:
        log_text: Raw log text (pasted or piped).
        file_path: Path to a log file on disk. Relative paths only.

    Returns:
        A dict representing either a DiagnosisResult or an ErrorResponse.
    """
    # Validate: at least one input required
    has_log_text = log_text is not None and log_text.strip() != ""
    has_file_path = file_path is not None and file_path.strip() != ""

    if not has_log_text and not has_file_path:
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message="Either 'log_text' or 'file_path' must be provided.",
        ).model_dump()

    # Read and combine inputs
    combined_parts: list[str] = []

    if has_file_path:
        # Validate file path
        err = _validate_file_path(file_path)
        if err:
            return err

        p = Path(file_path)
        if not p.exists():
            return ErrorResponse(
                error_code="FILE_NOT_FOUND",
                message=f"File not found: '{file_path}'",
            ).model_dump()

        try:
            combined_parts.append(p.read_text())
        except PermissionError:
            return ErrorResponse(
                error_code="FILE_NOT_READABLE",
                message=f"Permission denied: '{file_path}'",
            ).model_dump()

    if has_log_text:
        combined_parts.append(log_text)

    combined_text = "\n".join(combined_parts)

    # Parse and group
    entries = parse_log_lines(combined_text)
    raw_incidents = group_into_incidents(entries)
    provider_impact_raw = build_provider_impact(raw_incidents)

    # Build Incident models with runbook matching
    incidents: list[Incident] = []
    for raw in raw_incidents:
        status_code = raw.get("status_code")
        runbook = match_error_runbook(status_code) if status_code else None
        category = _classify_category(status_code, runbook)

        # Build diagnosis & action from runbook or defaults
        if runbook:
            diagnosis = runbook.get("description", "").strip()
            remediation = runbook.get("remediation", [])
            action = " ".join(remediation) if remediation else "Refer to runbook."
            runbook_ref = f"runbook://{runbook['id']}"

            # Fill draft response template
            template = runbook.get("draft_response_template")
            if template:
                draft_response = _fill_template(
                    template,
                    raw.get("client_id"),
                    raw["timestamp"],
                    raw.get("endpoint"),
                )
            else:
                draft_response = None
        else:
            diagnosis = f"Status code {status_code} received." if status_code else "Unknown error."
            action = "Investigate further."
            runbook_ref = None
            draft_response = None

        # Build attribution
        if category == "SERVER_SIDE":
            provider = raw.get("upstream_provider")
            if provider:
                attribution = (
                    f"Upstream provider '{provider}' failure. "
                    "This is a server-side dependency issue, not a client error."
                )
            else:
                attribution = "Server-side error. Not a client error."
        elif category == "CLIENT_SIDE":
            attribution = "Client-side error. The request was malformed or unauthorized."
        else:
            attribution = "Unable to determine attribution."

        incidents.append(Incident(
            timestamp=raw["timestamp"],
            client_id=raw.get("client_id"),
            endpoint=raw.get("endpoint"),
            status_code=status_code,
            category=category,
            attribution=attribution,
            upstream_provider=raw.get("upstream_provider"),
            diagnosis=diagnosis,
            action=action,
            draft_response=draft_response,
            runbook_ref=runbook_ref,
            log_lines=raw["log_lines"],
        ))

    # Build provider impact models
    provider_impact = {
        name: ProviderImpact(**data)
        for name, data in provider_impact_raw.items()
    }

    # Build summary
    server_side = sum(1 for i in incidents if i.category == "SERVER_SIDE")
    client_side = sum(1 for i in incidents if i.category == "CLIENT_SIDE")
    unknown = sum(1 for i in incidents if i.category == "UNKNOWN")

    observed_window = None
    if incidents:
        timestamps = [i.timestamp for i in incidents]
        observed_window = {"first": timestamps[0], "last": timestamps[-1]}

    summary = Summary(
        total_incidents=len(incidents),
        server_side=server_side,
        client_side=client_side,
        unknown=unknown,
        providers_involved=list(provider_impact_raw.keys()),
        observed_window=observed_window,
    )

    result = DiagnosisResult(
        incidents=incidents,
        provider_impact=provider_impact,
        summary=summary,
        timestamp=datetime.now(timezone.utc),
    )

    return result.model_dump()
