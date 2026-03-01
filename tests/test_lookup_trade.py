"""Tests for lookup_trade tool."""

import pytest

from zerohash_settlement_health.data_source.mock import MockDataSource
from zerohash_settlement_health.tools.lookup_trade import lookup_trade


@pytest.fixture
def ds():
    return MockDataSource()


class TestLookupTrade:
    def test_existing_trade(self, ds):
        result = lookup_trade(ds, "trade_001")
        assert result.get("error") is not True
        assert result["trade_id"] == "trade_001"
        assert result["trade_state"] == "terminated"
        assert result["settlement_state"] == "settled"
        assert result["participant_code"] == "PART_A"
        assert "trade_price" in result
        assert "trade_quantity" in result

    def test_all_mock_trades_exist(self, ds):
        for i in range(1, 9):
            trade_id = f"trade_00{i}"
            result = lookup_trade(ds, trade_id)
            assert result.get("error") is not True, f"Trade {trade_id} not found"
            assert result["trade_id"] == trade_id

    def test_nonexistent_trade(self, ds):
        result = lookup_trade(ds, "not_real")
        assert result["error"] is True
        assert result["error_code"] == "NOT_FOUND"
