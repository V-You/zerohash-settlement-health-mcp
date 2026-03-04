"""FastMCP server definition for the zerohash Settlement Health MCP.

This is the main entry point. It registers all tools and resources
with FastMCP and runs the server over stdio transport.
"""

from __future__ import annotations

import json
import logging
import warnings

# Suppress RequestsDependencyWarning caused by mcp-cli pulling in
# urllib3/chardet versions newer than requests' internal compat check.
# The warning is cosmetic — requests works fine with these versions.
warnings.filterwarnings("ignore", message="urllib3.*or chardet.*doesn't match")
from typing import Optional

from fastmcp import FastMCP

from zerohash_settlement_health.config import load_settings
from zerohash_settlement_health.data_source import create_data_source
from zerohash_settlement_health.runbooks import (
    get_all_runbooks,
    get_runbook,
    runbook_to_text,
)
from zerohash_settlement_health.tools.check_account_balance import (
    check_account_balance as _check_account_balance,
)
from zerohash_settlement_health.tools.check_settlement_health import (
    check_settlement_health as _check_settlement_health,
)
from zerohash_settlement_health.tools.get_market_prices import (
    get_market_prices as _get_market_prices,
)
from zerohash_settlement_health.tools.lookup_trade import (
    lookup_trade as _lookup_trade,
)

# ---------------------------------------------------------------------------
# Initialize
# ---------------------------------------------------------------------------
_settings = load_settings()

logging.basicConfig(level=getattr(logging, _settings.log_level, logging.INFO))
logger = logging.getLogger(__name__)

_data_source = create_data_source(_settings)

mcp = FastMCP(
    "zerohash Settlement Health MCP",
)

# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool
def check_settlement_health(
    trade_id: str,
    participant_code: Optional[str] = None,
) -> str:
    """Perform a settlement health diagnostic on a trade.

    Analyzes the trade's state and settlement status, matches it to a
    runbook, and returns a structured diagnosis with recommended actions.
    This is the primary tool for diagnosing settlement issues.

    Args:
        trade_id: The trade ID to diagnose (matches Zero Hash API trade_id).
        participant_code: Optional. If provided, also checks account balance
            and enriches the diagnosis. Validated against the trade's participant.
    """
    result = _check_settlement_health(
        _data_source, trade_id, participant_code,
        error_log_enabled=_settings.market_price_error_log,
    )
    return json.dumps(result, indent=2)


@mcp.tool
def lookup_trade(trade_id: str) -> str:
    """Look up raw trade data by trade ID.

    Returns the full trade payload including trade_state, settlement_state,
    trade_type, symbol, prices, quantities, and timestamps. Use this to
    inspect the raw API response and correlate with logs.

    Args:
        trade_id: The trade ID to look up.
    """
    result = _lookup_trade(_data_source, trade_id)
    return json.dumps(result, indent=2, default=str)


@mcp.tool
def check_account_balance(
    participant_code: str,
    asset: Optional[str] = None,
) -> str:
    """Check account balance for a participant.

    Returns balance and available_balance for each asset held by the
    participant. Use this to verify liquidity before or after settlement.

    Args:
        participant_code: The participant code to look up.
        asset: Optional asset filter (e.g., "BTC", "USD").
    """
    result = _check_account_balance(
        _data_source, participant_code, asset,
        error_log_enabled=_settings.market_price_error_log,
    )
    return json.dumps(result, indent=2)


@mcp.tool
def get_market_prices(
    assets: str = "BTC,ETH,SOL",
    vs_currency: str = "usd",
) -> str:
    """Get current market prices for crypto assets.

    Fetches real-time prices from CoinGecko (free, no API key required).
    Useful for contextualizing trade values and account balances during
    settlement investigations.

    Args:
        assets: Comma-separated asset symbols (e.g., "BTC,ETH,SOL").
        vs_currency: Quote currency for prices (default: "usd").
    """
    result = _get_market_prices(assets, vs_currency, _settings.market_price_error_log)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# MCP Resources — Runbooks
# ---------------------------------------------------------------------------

# Register each runbook as a static resource
for _rb_id, _rb_data in get_all_runbooks().items():

    # We need a closure to capture the current runbook data
    def _make_resource(rb_id: str, rb_data: dict):
        @mcp.resource(
            uri=f"runbook://{rb_id}",
            name=rb_data.get("title", rb_id),
            description=rb_data.get("description", "").strip()[:200],
            mime_type="text/plain",
        )
        def _resource() -> str:
            return runbook_to_text(rb_data)

    _make_resource(_rb_id, _rb_data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server."""
    logger.info(
        "Starting zerohash Settlement Health MCP server "
        f"(data_source={_settings.data_source})"
    )
    mcp.run()


if __name__ == "__main__":
    main()
