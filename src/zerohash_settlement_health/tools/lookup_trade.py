"""lookup_trade tool — raw trade data lookup."""

from __future__ import annotations

from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.models import ErrorResponse


def lookup_trade(data_source: DataSource, trade_id: str) -> dict:
    """Look up raw trade data by trade ID.

    Args:
        data_source: The data source to query.
        trade_id: The trade ID to look up.

    Returns:
        A dict with the full trade payload, or an error response.
    """
    trade = data_source.get_trade(trade_id)
    if trade is None:
        return ErrorResponse(
            error_code="NOT_FOUND",
            message=f"No trade found for trade_id '{trade_id}'.",
        ).model_dump()

    return trade.model_dump(mode="json")
