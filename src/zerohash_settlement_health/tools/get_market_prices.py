"""get_market_prices tool — live crypto market price lookup."""

from __future__ import annotations

from datetime import datetime, timezone

from zerohash_settlement_health.market_data import fetch_prices
from zerohash_settlement_health.models import ErrorResponse
from zerohash_settlement_health.models.market import MarketPriceResult


def get_market_prices(
    assets: str = "BTC,ETH,SOL",
    vs_currency: str = "usd",
    error_log_enabled: bool = False,
) -> dict:
    """Get current market prices for crypto assets.

    Args:
        assets: Comma-separated asset symbols (e.g., "BTC,ETH,SOL").
        vs_currency: Quote currency (default: "usd").
        error_log_enabled: Whether to log errors to market_errors.log.

    Returns:
        A dict with market prices, or an error response.
    """
    symbols = [s.strip() for s in assets.split(",") if s.strip()]
    if not symbols:
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message="No asset symbols provided. Use comma-separated symbols like 'BTC,ETH,SOL'.",
        ).model_dump()

    prices = fetch_prices(symbols, vs_currency, error_log_enabled)

    if not prices:
        return ErrorResponse(
            error_code="EXTERNAL_API_ERROR",
            message="Failed to fetch market prices. The CoinGecko API may be unreachable or the symbols are not recognized.",
        ).model_dump()

    return MarketPriceResult(
        prices=list(prices.values()),
        vs_currency=vs_currency,
        source="coingecko",
        timestamp=datetime.now(timezone.utc),
    ).model_dump(mode="json")
