"""Tests for error handling across all tools."""

import pytest

from zerohash_settlement_health.data_source.mock import MockDataSource
from zerohash_settlement_health.tools.check_account_balance import check_account_balance
from zerohash_settlement_health.tools.check_settlement_health import check_settlement_health
from zerohash_settlement_health.tools.lookup_trade import lookup_trade


@pytest.fixture
def ds():
    return MockDataSource()


class TestErrorResponses:
    """All NOT_FOUND errors should have a consistent structure."""

    def test_health_check_not_found(self, ds):
        result = check_settlement_health(ds, "nonexistent_trade")
        assert result["error"] is True
        assert result["error_code"] == "NOT_FOUND"
        assert "message" in result
        assert "nonexistent_trade" in result["message"]

    def test_lookup_not_found(self, ds):
        result = lookup_trade(ds, "nonexistent_trade")
        assert result["error"] is True
        assert result["error_code"] == "NOT_FOUND"
        assert "message" in result

    def test_balance_not_found(self, ds):
        result = check_account_balance(ds, "NOBODY")
        assert result["error"] is True
        assert result["error_code"] == "NOT_FOUND"
        assert "message" in result

    def test_health_check_invalid_participant(self, ds):
        result = check_settlement_health(ds, "trade_001", participant_code="WRONG")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"
        assert "WRONG" in result["message"]
        assert "PART_A" in result["message"]

    def test_error_response_structure(self, ds):
        """Verify error responses always have exactly these fields."""
        result = lookup_trade(ds, "nope")
        assert set(result.keys()) == {"error", "error_code", "message"}
