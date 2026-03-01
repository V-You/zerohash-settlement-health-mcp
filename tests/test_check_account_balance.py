"""Tests for check_account_balance tool."""

import pytest

from zerohash_settlement_health.data_source.mock import MockDataSource
from zerohash_settlement_health.tools.check_account_balance import (
    check_account_balance,
)


@pytest.fixture
def ds():
    return MockDataSource()


class TestCheckAccountBalance:
    def test_existing_participant(self, ds):
        result = check_account_balance(ds, "PART_A")
        assert result.get("error") is not True
        assert result["participant_code"] == "PART_A"
        assert len(result["accounts"]) == 3  # BTC, ETH, USD

    def test_asset_filter(self, ds):
        result = check_account_balance(ds, "PART_A", asset="BTC")
        assert result.get("error") is not True
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["asset"] == "BTC"

    def test_asset_filter_case_insensitive(self, ds):
        result = check_account_balance(ds, "PART_A", asset="btc")
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["asset"] == "BTC"

    def test_zero_balance_participant(self, ds):
        """PART_C has zero available balance."""
        result = check_account_balance(ds, "PART_C")
        assert result.get("error") is not True
        btc = [a for a in result["accounts"] if a["asset"] == "BTC"][0]
        assert btc["available_balance"] == "0.00000000"

    def test_nonexistent_participant(self, ds):
        result = check_account_balance(ds, "NOBODY")
        assert result["error"] is True
        assert result["error_code"] == "NOT_FOUND"

    def test_asset_filter_no_match(self, ds):
        result = check_account_balance(ds, "PART_A", asset="DOGE")
        assert result.get("error") is not True
        assert len(result["accounts"]) == 0
