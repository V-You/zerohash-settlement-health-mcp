"""Log parser for API error logs.

Parses [HH:MM:SS] LEVEL: message format, groups entries into
incidents, and builds provider impact summaries.
"""

from __future__ import annotations

import re
from typing import Optional

from zerohash_settlement_health.models.incident import LogEntry


# Matches: [14:38:01] ERROR: Some message here
_LOG_LINE_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.*)$")

# Extract client_id from message: "from Client_882" or "to Client_882"
_CLIENT_RE = re.compile(r"(?:from|to)\s+(Client_\w+)")

# Extract endpoint: "POST /liquidity/rfq" or "GET /something"
_ENDPOINT_RE = re.compile(r"(?:Received\s+)?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/\S+)")

# Extract status code: "Returning 503 Service Unavailable" or "HTTP 503"
_STATUS_CODE_RE = re.compile(r"(?:Returning|HTTP)\s+(\d{3})\b")

# Extract upstream provider: "provider 'PrimeX'" or "provider \"PrimeX\""
_PROVIDER_RE = re.compile(r"provider\s+['\"](\w+)['\"]")


def parse_log_lines(text: str) -> list[LogEntry]:
    """Parse raw log text into structured LogEntry objects.

    Only lines matching [HH:MM:SS] LEVEL: message are parsed.
    Non-matching lines are silently skipped.
    """
    entries: list[LogEntry] = []

    for line in text.splitlines():
        line = line.strip()
        m = _LOG_LINE_RE.match(line)
        if not m:
            continue

        timestamp, level, message = m.group(1), m.group(2), m.group(3)

        client_match = _CLIENT_RE.search(message)
        endpoint_match = _ENDPOINT_RE.search(message)
        status_match = _STATUS_CODE_RE.search(message)
        provider_match = _PROVIDER_RE.search(message)

        entries.append(LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            client_id=client_match.group(1) if client_match else None,
            endpoint=f"{endpoint_match.group(1)} {endpoint_match.group(2)}" if endpoint_match else None,
            status_code=int(status_match.group(1)) if status_match else None,
            upstream_provider=provider_match.group(1) if provider_match else None,
        ))

    return entries


def _time_to_seconds(ts: str) -> int:
    """Convert HH:MM:SS to seconds since midnight."""
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def group_into_incidents(
    entries: list[LogEntry],
) -> list[dict]:
    """Group log entries into incidents.

    Entries sharing the same (client_id, endpoint) within a ≤2s window
    are grouped into one incident. Returns a list of dicts with
    aggregated fields ready for Incident model construction.
    """
    if not entries:
        return []

    # Collect entries into buckets by (client_id, endpoint)
    buckets: dict[tuple[Optional[str], Optional[str]], list[LogEntry]] = {}
    for entry in entries:
        key = (entry.client_id, entry.endpoint)
        buckets.setdefault(key, []).append(entry)

    # Merge partial-key buckets into the nearest full-key bucket.
    # A partial key has at least one None component (e.g. (Client_882, None)
    # or (None, None)). We merge into a bucket with a matching non-None
    # component within a ≤2s window.
    partial_keys = [k for k in buckets if k[0] is None or k[1] is None]
    for pk in partial_keys:
        orphans = buckets.pop(pk)
        for orphan in orphans:
            orphan_sec = _time_to_seconds(orphan.timestamp)
            best_key = None
            best_diff = float("inf")
            for key, bucket_entries in buckets.items():
                # Skip other partial-key buckets
                if key[0] is None or key[1] is None:
                    continue
                # Check compatibility: matching client_id or endpoint
                if pk[0] is not None and pk[0] != key[0]:
                    continue
                if pk[1] is not None and pk[1] != key[1]:
                    continue
                for be in bucket_entries:
                    diff = abs(_time_to_seconds(be.timestamp) - orphan_sec)
                    if diff <= 2 and diff < best_diff:
                        best_diff = diff
                        best_key = key
            if best_key is not None:
                buckets[best_key].append(orphan)
            # else: orphan dropped (no matching bucket within window)

    # Within each bucket, split into sub-groups if timestamps are >2s apart
    raw_incidents: list[list[LogEntry]] = []
    for _key, bucket_entries in buckets.items():
        bucket_entries.sort(key=lambda e: _time_to_seconds(e.timestamp))
        current_group: list[LogEntry] = [bucket_entries[0]]
        for entry in bucket_entries[1:]:
            if _time_to_seconds(entry.timestamp) - _time_to_seconds(current_group[0].timestamp) <= 2:
                current_group.append(entry)
            else:
                raw_incidents.append(current_group)
                current_group = [entry]
        raw_incidents.append(current_group)

    # Sort incidents by first timestamp
    raw_incidents.sort(key=lambda g: _time_to_seconds(g[0].timestamp))

    # Flatten each group into an incident dict
    incidents = []
    for group in raw_incidents:
        # Aggregate fields from all entries in the group
        timestamp = group[0].timestamp
        client_id = _first_non_none(e.client_id for e in group)
        endpoint = _first_non_none(e.endpoint for e in group)
        status_code = _first_non_none(e.status_code for e in group)
        upstream_provider = _first_non_none(e.upstream_provider for e in group)

        # Reconstruct original log lines
        log_lines = [
            f"[{e.timestamp}] {e.level}: {e.message}"
            for e in group
        ]

        incidents.append({
            "timestamp": timestamp,
            "client_id": client_id,
            "endpoint": endpoint,
            "status_code": status_code,
            "upstream_provider": upstream_provider,
            "log_lines": log_lines,
        })

    return incidents


def _first_non_none(values):
    """Return the first non-None value from an iterable, or None."""
    for v in values:
        if v is not None:
            return v
    return None


def build_provider_impact(
    incidents: list[dict],
) -> dict[str, dict]:
    """Aggregate provider impact across all incidents.

    Returns a dict keyed by provider name with affected_clients,
    incident_count, first_seen, and last_seen.
    """
    impact: dict[str, dict] = {}

    for inc in incidents:
        provider = inc.get("upstream_provider")
        if not provider:
            continue

        if provider not in impact:
            impact[provider] = {
                "affected_clients": [],
                "incident_count": 0,
                "first_seen": inc["timestamp"],
                "last_seen": inc["timestamp"],
            }

        entry = impact[provider]
        entry["incident_count"] += 1
        entry["last_seen"] = inc["timestamp"]

        client = inc.get("client_id")
        if client and client not in entry["affected_clients"]:
            entry["affected_clients"].append(client)

    return impact
