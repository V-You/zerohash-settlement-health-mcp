"""Pydantic models for error log diagnosis."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LogEntry(BaseModel):
    """A single parsed log line."""

    timestamp: str
    level: str
    message: str
    client_id: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    upstream_provider: Optional[str] = None


class Incident(BaseModel):
    """A grouped incident derived from one or more log entries."""

    timestamp: str
    client_id: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    category: str  # "CLIENT_SIDE" | "SERVER_SIDE" | "UNKNOWN"
    attribution: str
    upstream_provider: Optional[str] = None
    diagnosis: str
    action: str
    draft_response: Optional[str] = None
    runbook_ref: Optional[str] = None
    log_lines: list[str]


class ProviderImpact(BaseModel):
    """Aggregated impact for a single upstream provider."""

    affected_clients: list[str]
    incident_count: int
    first_seen: str
    last_seen: str


class Summary(BaseModel):
    """High-level summary of all diagnosed incidents."""

    total_incidents: int
    server_side: int
    client_side: int
    unknown: int
    providers_involved: list[str]
    observed_window: Optional[dict] = None


class DiagnosisResult(BaseModel):
    """Complete output of the diagnose_errors tool."""

    incidents: list[Incident]
    provider_impact: dict[str, ProviderImpact]
    summary: Summary
    timestamp: datetime
