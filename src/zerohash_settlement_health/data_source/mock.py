"""Mock data source with realistic Zero Hash API scenarios.

Provides hardcoded trade and account data covering all trade_state × settlement_state
combinations for comprehensive diagnostic testing.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.models import (
    Account,
    AccountBalanceResult,
    Trade,
)

# ---------------------------------------------------------------------------
# Mock Trades — one per trade_state × settlement_state combination
# ---------------------------------------------------------------------------
_NOW = datetime(2026, 2, 27, 21, 0, 0)

_MOCK_TRADES: dict[str, Trade] = {
    # HEALTHY: terminated + settled
    "trade_001": Trade(
        trade_id="trade_001",
        trade_state="terminated",
        settlement_state="settled",
        trade_type="regular",
        symbol="BTC/USD",
        trade_price="43250.00",
        trade_quantity="0.50000000",
        participant_code="PART_A",
        account_group="GRP_001",
        created_at=_NOW - timedelta(hours=2),
        updated_at=_NOW - timedelta(minutes=30),
    ),
    # UNHEALTHY CRITICAL: terminated + defaulted
    "trade_002": Trade(
        trade_id="trade_002",
        trade_state="terminated",
        settlement_state="defaulted",
        trade_type="regular",
        symbol="ETH/USD",
        trade_price="2310.00",
        trade_quantity="10.00000000",
        participant_code="PART_B",
        account_group="GRP_002",
        created_at=_NOW - timedelta(hours=5),
        updated_at=_NOW - timedelta(hours=1),
    ),
    # UNHEALTHY CRITICAL: terminated + counterparty_defaulted
    "trade_003": Trade(
        trade_id="trade_003",
        trade_state="terminated",
        settlement_state="counterparty_defaulted",
        trade_type="regular",
        symbol="BTC/USD",
        trade_price="43100.00",
        trade_quantity="1.00000000",
        participant_code="PART_A",
        account_group="GRP_001",
        created_at=_NOW - timedelta(hours=3),
        updated_at=_NOW - timedelta(hours=1),
    ),
    # UNHEALTHY HIGH: active + obligations_outstanding
    "trade_004": Trade(
        trade_id="trade_004",
        trade_state="active",
        settlement_state="obligations_outstanding",
        trade_type="regular",
        symbol="BTC/USD",
        trade_price="43500.00",
        trade_quantity="0.25000000",
        participant_code="PART_C",
        account_group="GRP_003",
        created_at=_NOW - timedelta(minutes=45),
        updated_at=_NOW - timedelta(minutes=10),
    ),
    # PENDING MEDIUM: active + current_obligations_met
    "trade_005": Trade(
        trade_id="trade_005",
        trade_state="active",
        settlement_state="current_obligations_met",
        trade_type="regular",
        symbol="ETH/USD",
        trade_price="2295.00",
        trade_quantity="5.00000000",
        participant_code="PART_A",
        account_group="GRP_001",
        created_at=_NOW - timedelta(minutes=20),
        updated_at=_NOW - timedelta(minutes=5),
    ),
    # PENDING LOW: accepted + null
    "trade_006": Trade(
        trade_id="trade_006",
        trade_state="accepted",
        settlement_state=None,
        trade_type="regular",
        symbol="SOL/USD",
        trade_price="98.50",
        trade_quantity="100.00000000",
        participant_code="PART_B",
        account_group="GRP_002",
        created_at=_NOW - timedelta(minutes=2),
        updated_at=_NOW - timedelta(minutes=1),
    ),
    # UNKNOWN: unexpected combo — terminated + obligations_outstanding
    "trade_007": Trade(
        trade_id="trade_007",
        trade_state="terminated",
        settlement_state="obligations_outstanding",
        trade_type="regular",
        symbol="BTC/USD",
        trade_price="43000.00",
        trade_quantity="0.10000000",
        participant_code="PART_C",
        account_group="GRP_003",
        created_at=_NOW - timedelta(hours=6),
        updated_at=_NOW - timedelta(hours=2),
    ),
    # UNKNOWN: unexpected combo — accepted + settled
    "trade_008": Trade(
        trade_id="trade_008",
        trade_state="accepted",
        settlement_state="settled",
        trade_type="regular",
        symbol="ETH/USD",
        trade_price="2300.00",
        trade_quantity="2.00000000",
        participant_code="PART_A",
        account_group="GRP_001",
        created_at=_NOW - timedelta(hours=1),
        updated_at=_NOW - timedelta(minutes=30),
    ),
}

# ---------------------------------------------------------------------------
# Mock Account Balances — per participant
# ---------------------------------------------------------------------------
_MOCK_ACCOUNTS: dict[str, list[Account]] = {
    "PART_A": [
        Account(
            asset="BTC",
            balance="1.50000000",
            available_balance="1.25000000",
            account_group="GRP_001",
        ),
        Account(
            asset="ETH",
            balance="15.00000000",
            available_balance="12.50000000",
            account_group="GRP_001",
        ),
        Account(
            asset="USD",
            balance="50000.00",
            available_balance="48500.00",
            account_group="GRP_001",
        ),
    ],
    "PART_B": [
        Account(
            asset="ETH",
            balance="25.00000000",
            available_balance="20.00000000",
            account_group="GRP_002",
        ),
        Account(
            asset="SOL",
            balance="500.00000000",
            available_balance="450.00000000",
            account_group="GRP_002",
        ),
        Account(
            asset="USD",
            balance="100000.00",
            available_balance="85000.00",
            account_group="GRP_002",
        ),
    ],
    "PART_C": [
        Account(
            asset="BTC",
            balance="0.10000000",
            available_balance="0.00000000",
            account_group="GRP_003",
        ),
        Account(
            asset="USD",
            balance="500.00",
            available_balance="0.00",
            account_group="GRP_003",
        ),
    ],
}


class MockDataSource(DataSource):
    """Mock data source returning hardcoded realistic trade and account data.

    Includes scenarios for all trade_state × settlement_state combinations.
    PART_C has zero available balance to simulate insufficient liquidity.
    """

    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Look up a mock trade by ID."""
        return _MOCK_TRADES.get(trade_id)

    def get_account_balance(
        self, participant_code: str, asset: Optional[str] = None
    ) -> Optional[AccountBalanceResult]:
        """Look up mock account balances for a participant."""
        accounts = _MOCK_ACCOUNTS.get(participant_code)
        if accounts is None:
            return None

        if asset:
            accounts = [a for a in accounts if a.asset.upper() == asset.upper()]

        return AccountBalanceResult(
            participant_code=participant_code,
            accounts=accounts,
        )
