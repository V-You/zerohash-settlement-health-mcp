"""Runbook loader and matching logic.

Loads YAML runbook files from the data/ directory and provides
matching by trade_state + settlement_state combinations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml


_RUNBOOKS_DIR = Path(__file__).parent / "data"

# Loaded runbooks keyed by id
_runbooks: dict[str, dict[str, Any]] = {}

# Lookup table: (trade_state, settlement_state) -> runbook id
_trigger_index: dict[tuple[str, str], str] = {}


def _load_runbooks() -> None:
    """Load all YAML runbook files from the data directory."""
    global _runbooks, _trigger_index
    _runbooks = {}
    _trigger_index = {}

    for yaml_file in sorted(_RUNBOOKS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        runbook_id = data["id"]
        _runbooks[runbook_id] = data

        # Build trigger index (skip wildcard triggers — they're fallbacks)
        trigger = data.get("trigger", {})
        ts = trigger.get("trade_state", "*")
        ss = trigger.get("settlement_state", "*")
        if ts != "*" and ss != "*":
            _trigger_index[(ts, ss)] = runbook_id


def get_all_runbooks() -> dict[str, dict[str, Any]]:
    """Return all loaded runbooks."""
    if not _runbooks:
        _load_runbooks()
    return _runbooks


def get_runbook(runbook_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a specific runbook by ID."""
    if not _runbooks:
        _load_runbooks()
    return _runbooks.get(runbook_id)


def match_runbook(
    trade_state: str, settlement_state: Optional[str]
) -> Optional[dict[str, Any]]:
    """Find the runbook matching a given trade_state × settlement_state combination.

    Falls back to the 'unknown_state' runbook if no specific match is found.
    """
    if not _runbooks:
        _load_runbooks()

    ss = settlement_state or "null"  # None -> "null" for matching
    key = (trade_state, ss)

    runbook_id = _trigger_index.get(key)
    if runbook_id:
        return _runbooks[runbook_id]

    # Fallback to unknown_state
    return _runbooks.get("unknown_state")


def runbook_to_text(runbook: dict[str, Any]) -> str:
    """Format a runbook as human-readable text for the LLM."""
    lines = [
        f"# {runbook['title']}",
        f"Severity: {runbook['severity']}",
        "",
        runbook.get("description", "").strip(),
        "",
        "## Diagnosis Steps",
    ]
    for step in runbook.get("diagnosis_steps", []):
        lines.append(f"  - {step}")

    lines.append("")
    lines.append("## Remediation")
    for step in runbook.get("remediation", []):
        lines.append(f"  - {step}")

    lines.append("")
    lines.append("## API References")
    for ref in runbook.get("api_references", []):
        lines.append(f"  - {ref}")

    return "\n".join(lines)
