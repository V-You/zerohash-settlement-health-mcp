"""Abstract base class for data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from zerohash_settlement_health.models import AccountBalanceResult, Trade


class DataSource(ABC):
    """Abstract interface for querying trade and account data.

    Implementations:
    - MockDataSource: returns hardcoded realistic scenarios (V1)
    - LiveDataSource: queries the Zero Hash CERT/PROD API (V2)
    """

    @abstractmethod
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Retrieve a trade by its ID.

        Returns None if the trade does not exist.
        """

    @abstractmethod
    def get_account_balance(
        self, participant_code: str, asset: Optional[str] = None
    ) -> Optional[AccountBalanceResult]:
        """Retrieve account balances for a participant.

        If asset is provided, filter to that asset only.
        Returns None if the participant does not exist.
        """
