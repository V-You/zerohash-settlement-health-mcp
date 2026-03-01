"""check_account_balance tool — participant balance lookup."""

from __future__ import annotations

from typing import Optional

from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.models import ErrorResponse


def check_account_balance(
    data_source: DataSource,
    participant_code: str,
    asset: Optional[str] = None,
) -> dict:
    """Check account balance for a participant.

    Args:
        data_source: The data source to query.
        participant_code: The participant code to filter by.
        asset: Optional asset filter (e.g., "BTC", "USD").

    Returns:
        A dict with account balances, or an error response.
    """
    result = data_source.get_account_balance(participant_code, asset)
    if result is None:
        return ErrorResponse(
            error_code="NOT_FOUND",
            message=f"No accounts found for participant_code '{participant_code}'.",
        ).model_dump()

    return result.model_dump(mode="json")
