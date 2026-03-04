"""CoinGecko market data client with optional local error logging."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from zerohash_settlement_health.models.market import MarketPrice

logger = logging.getLogger(__name__)

# Static mapping of common asset symbols to CoinGecko IDs.
SYMBOL_TO_COINGECKO_ID: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "USDC": "usd-coin",
    "USDT": "tether",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "LTC": "litecoin",
}

_COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3/simple/price"
_TIMEOUT_SECONDS = 5
_LOG_FILE = Path(__file__).parent.parent.parent / "market_errors.log"


def _log_error(error_type: str, message: str) -> None:
    """Append a structured error line to market_errors.log."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] ERROR source=coingecko type={error_type} message={message}\n"
    try:
        with open(_LOG_FILE, "a") as f:
            f.write(line)
    except OSError:
        logger.warning("Failed to write to market_errors.log")


def fetch_prices(
    symbols: list[str],
    vs_currency: str = "usd",
    error_log_enabled: bool = False,
) -> dict[str, MarketPrice]:
    """Fetch current prices from CoinGecko for the given asset symbols.

    Returns a dict mapping symbol -> MarketPrice. Returns an empty dict
    on any failure (never raises).
    """
    # Map symbols to CoinGecko IDs, skipping unknowns
    id_to_symbol: dict[str, str] = {}
    for sym in symbols:
        upper = sym.upper()
        cg_id = SYMBOL_TO_COINGECKO_ID.get(upper)
        if cg_id:
            id_to_symbol[cg_id] = upper

    if not id_to_symbol:
        return {}

    params = {
        "ids": ",".join(id_to_symbol.keys()),
        "vs_currencies": vs_currency,
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }

    try:
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            response = client.get(_COINGECKO_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        msg = f"Request timed out after {_TIMEOUT_SECONDS}s"
        logger.warning("CoinGecko API timeout: %s", msg)
        if error_log_enabled:
            _log_error("timeout", msg)
        return {}
    except httpx.HTTPStatusError as exc:
        msg = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        logger.warning("CoinGecko API HTTP error: %s", msg)
        if error_log_enabled:
            _log_error("http_error", msg)
        return {}
    except httpx.ConnectError as exc:
        msg = str(exc)[:200]
        logger.warning("CoinGecko API connection error: %s", msg)
        if error_log_enabled:
            _log_error("connection_error", msg)
        return {}
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"[:200]
        logger.warning("CoinGecko API unexpected error: %s", msg)
        if error_log_enabled:
            _log_error("unknown", msg)
        return {}

    # Parse the response into MarketPrice objects
    result: dict[str, MarketPrice] = {}
    for cg_id, symbol in id_to_symbol.items():
        price_data = data.get(cg_id)
        if not price_data:
            continue

        price = price_data.get(vs_currency)
        if price is None:
            continue

        change_24h = price_data.get(f"{vs_currency}_24h_change")
        last_updated_ts = price_data.get("last_updated_at")

        last_updated: Optional[datetime] = None
        if last_updated_ts:
            last_updated = datetime.fromtimestamp(last_updated_ts, tz=timezone.utc)

        result[symbol] = MarketPrice(
            asset=symbol,
            price_usd=f"{price}",
            change_24h_pct=f"{change_24h:.2f}" if change_24h is not None else None,
            last_updated=last_updated,
        )

    return result
