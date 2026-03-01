"""Live Zero Hash API data source (V2 — stub).

This module will implement the live Zero Hash API client using HMAC-SHA256
authentication when CERT API keys become available. For now, it raises
NotImplementedError to clearly indicate it is not yet implemented.
"""

from __future__ import annotations

from typing import Optional

from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.models import AccountBalanceResult, Trade


class LiveDataSource(DataSource):
    """Live Zero Hash API client (V2 — not yet implemented).

    Will implement HMAC-SHA256 authentication per:
    https://docs.zerohash.com/reference/api-authentication
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        api_passphrase: str,
        base_url: str = "https://api.cert.zerohash.com",
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._api_passphrase = api_passphrase
        self._base_url = base_url.rstrip("/")

    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Query GET /trades/:trade_id on the Zero Hash API."""
        raise NotImplementedError(
            "Live API integration is not yet available. "
            "Set ZEROHASH_DATA_SOURCE=mock to use the mock data source."
        )

    def get_account_balance(
        self, participant_code: str, asset: Optional[str] = None
    ) -> Optional[AccountBalanceResult]:
        """Query GET /accounts on the Zero Hash API."""
        raise NotImplementedError(
            "Live API integration is not yet available. "
            "Set ZEROHASH_DATA_SOURCE=mock to use the mock data source."
        )
