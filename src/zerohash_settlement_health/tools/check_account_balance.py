"""check_account_balance tool — participant balance lookup."""

from __future__ import annotations

import logging
from typing import Optional

from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.market_data import fetch_prices
from zerohash_settlement_health.models import ErrorResponse

logger = logging.getLogger(__name__)

_FIAT_SYMBOLS = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}


def check_account_balance(
    data_source: DataSource,
    participant_code: str,
    asset: Optional[str] = None,
    error_log_enabled: bool = False,
) -> dict:
    """Check account balance for a participant.

    Args:
        data_source: The data source to query.
        participant_code: The participant code to filter by.
        asset: Optional asset filter (e.g., "BTC", "USD").
        error_log_enabled: Whether to log price API errors to file.

    Returns:
        A dict with account balances, or an error response.
    """
    result = data_source.get_account_balance(participant_code, asset)
    if result is None:
        return ErrorResponse(
            error_code="NOT_FOUND",
            message=f"No accounts found for participant_code '{participant_code}'.",
        ).model_dump()

    output = result.model_dump(mode="json")

    # Enrich with market prices for non-fiat assets
    crypto_symbols = [
        a["asset"] for a in output.get("accounts", [])
        if a["asset"].upper() not in _FIAT_SYMBOLS
    ]
    if crypto_symbols:
        prices = fetch_prices(crypto_symbols, error_log_enabled=error_log_enabled)
        for account in output.get("accounts", []):
            sym = account["asset"].upper()
            if sym in prices:
                price = float(prices[sym].price_usd)
                balance = float(account["balance"])
                account["price_usd"] = prices[sym].price_usd
                account["value_usd"] = f"{balance * price:.2f}"

    return output
