"""Pydantic models for Zero Hash trade data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TradeState(str, Enum):
    """Possible trade_state values from the Zero Hash API."""

    ACCEPTED = "accepted"
    ACTIVE = "active"
    TERMINATED = "terminated"


class SettlementState(str, Enum):
    """Possible settlement_state values from the Zero Hash API."""

    NULL = "null"
    OBLIGATIONS_OUTSTANDING = "obligations_outstanding"
    CURRENT_OBLIGATIONS_MET = "current_obligations_met"
    SETTLED = "settled"
    DEFAULTED = "defaulted"
    COUNTERPARTY_DEFAULTED = "counterparty_defaulted"


class Trade(BaseModel):
    """Represents a Zero Hash trade."""

    trade_id: str = Field(..., description="Unique trade identifier")
    trade_state: TradeState = Field(..., description="Current state of the trade")
    settlement_state: Optional[SettlementState] = Field(
        None, description="Current settlement state"
    )
    trade_type: str = Field(default="regular", description="Type of trade")
    symbol: str = Field(default="BTC/USD", description="Trading pair symbol")
    trade_price: str = Field(default="0.00", description="Execution price")
    trade_quantity: str = Field(default="0.00", description="Trade quantity")
    participant_code: str = Field(..., description="Participant who submitted the trade")
    account_group: str = Field(default="", description="Account group identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Trade creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = {"use_enum_values": True}


class HealthStatus(str, Enum):
    """Diagnostic health status for a trade."""

    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    """Severity levels for diagnostics."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HealthCheckResult(BaseModel):
    """Result of a settlement health check."""

    trade_id: str
    status: HealthStatus
    trade_state: str
    settlement_state: Optional[str]
    participant_code: str
    diagnosis: str
    action: str
    runbook_ref: Optional[str] = None
    severity: Severity
    market_context: Optional[dict] = Field(default=None, description="Live market price context for the trade's asset")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}


class ErrorResponse(BaseModel):
    """Standard error response for all tools."""

    error: bool = True
    error_code: str
    message: str
