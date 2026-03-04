"""check_settlement_health tool — the flagship diagnostic tool."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.market_data import fetch_prices
from zerohash_settlement_health.models import (
    ErrorResponse,
    HealthCheckResult,
    HealthStatus,
    Severity,
)
from zerohash_settlement_health.runbooks import match_runbook


# Diagnostic logic table: (trade_state, settlement_state) -> (status, severity)
_DIAGNOSTIC_TABLE: dict[tuple[str, Optional[str]], tuple[HealthStatus, Severity]] = {
    ("terminated", "settled"): (HealthStatus.HEALTHY, Severity.INFO),
    ("terminated", "defaulted"): (HealthStatus.UNHEALTHY, Severity.CRITICAL),
    ("terminated", "counterparty_defaulted"): (HealthStatus.UNHEALTHY, Severity.CRITICAL),
    ("active", "obligations_outstanding"): (HealthStatus.UNHEALTHY, Severity.HIGH),
    ("active", "current_obligations_met"): (HealthStatus.PENDING, Severity.MEDIUM),
    ("accepted", "null"): (HealthStatus.PENDING, Severity.LOW),
    ("accepted", None): (HealthStatus.PENDING, Severity.LOW),
}


def check_settlement_health(
    data_source: DataSource,
    trade_id: str,
    participant_code: Optional[str] = None,
    error_log_enabled: bool = False,
) -> dict:
    """Perform a settlement health diagnostic on a trade.

    Args:
        data_source: The data source to query.
        trade_id: The trade ID to diagnose.
        participant_code: Optional participant code. If provided, validates
            against the trade and enriches the diagnosis with balance info.
        error_log_enabled: Whether to log price API errors to file.

    Returns:
        A dict representing either a HealthCheckResult or an ErrorResponse.
    """
    # 1. Look up the trade
    trade = data_source.get_trade(trade_id)
    if trade is None:
        return ErrorResponse(
            error_code="NOT_FOUND",
            message=f"No trade found for trade_id '{trade_id}'.",
        ).model_dump()

    # 2. Validate participant_code if provided
    actual_participant = trade.participant_code
    if participant_code and participant_code != actual_participant:
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message=(
                f"Provided participant_code '{participant_code}' does not match "
                f"trade's participant_code '{actual_participant}'."
            ),
        ).model_dump()

    # Use the trade's participant_code (derived if not provided)
    effective_participant = participant_code or actual_participant

    # 3. Determine health status and severity
    ss = trade.settlement_state
    key = (trade.trade_state, ss)
    status, severity = _DIAGNOSTIC_TABLE.get(
        key, (HealthStatus.UNKNOWN, Severity.HIGH)
    )

    # 4. Match runbook (skip for healthy trades — no remediation needed)
    if status == HealthStatus.HEALTHY:
        runbook = None
        runbook_ref = None
    else:
        runbook = match_runbook(trade.trade_state, ss)
        runbook_ref = f"runbook://{runbook['id']}" if runbook else None

    # 5. Build diagnosis and action text
    diagnosis, action = _build_diagnosis(trade, status, runbook)

    # 6. Enrich with balance info if participant_code was provided
    if participant_code:
        balance_result = data_source.get_account_balance(effective_participant)
        if balance_result and balance_result.accounts:
            balance_summary = ", ".join(
                f"{a.asset}: {a.available_balance} available"
                for a in balance_result.accounts
            )
            diagnosis += f" Participant balances: [{balance_summary}]."

    # 7. Enrich with market context
    market_context = None
    base_asset = trade.symbol.split("/")[0] if "/" in trade.symbol else trade.symbol
    prices = fetch_prices([base_asset], error_log_enabled=error_log_enabled)
    if base_asset.upper() in prices:
        current_price = float(prices[base_asset.upper()].price_usd)
        trade_price = float(trade.trade_price)
        if trade_price > 0:
            diff_pct = ((current_price - trade_price) / trade_price) * 100
            sign = "+" if diff_pct >= 0 else ""
            market_context = {
                "asset": base_asset.upper(),
                "current_price_usd": prices[base_asset.upper()].price_usd,
                "trade_price": trade.trade_price,
                "price_diff_pct": f"{sign}{diff_pct:.2f}",
            }
        else:
            market_context = {
                "asset": base_asset.upper(),
                "current_price_usd": prices[base_asset.upper()].price_usd,
                "trade_price": trade.trade_price,
            }

    return HealthCheckResult(
        trade_id=trade_id,
        status=status,
        trade_state=trade.trade_state,
        settlement_state=ss,
        participant_code=effective_participant,
        diagnosis=diagnosis,
        action=action,
        runbook_ref=runbook_ref,
        severity=severity,
        market_context=market_context,
        timestamp=datetime.now(timezone.utc),
    ).model_dump(mode="json")


def _build_diagnosis(trade, status: HealthStatus, runbook) -> tuple[str, str]:
    """Build human-readable diagnosis and action strings."""
    ts = trade.trade_state
    ss = trade.settlement_state or "null"

    if status == HealthStatus.HEALTHY:
        return (
            f"Trade is {ts} and settlement is {ss}. All obligations fulfilled.",
            "No action required.",
        )

    if runbook:
        desc = runbook.get("description", "").strip()
        remediation = runbook.get("remediation", [])
        action = " ".join(remediation) if remediation else "Review the matched runbook for remediation steps."
        return (desc, action)

    return (
        f"Trade is in state '{ts}' with settlement state '{ss}'. "
        "This combination is unexpected and could not be matched to a known runbook.",
        "Escalate to the engineering team with the full trade payload.",
    )
