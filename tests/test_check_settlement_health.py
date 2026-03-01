"""Tests for check_settlement_health tool."""

import pytest

from zerohash_settlement_health.data_source.mock import MockDataSource
from zerohash_settlement_health.tools.check_settlement_health import (
    check_settlement_health,
)


@pytest.fixture
def ds():
    return MockDataSource()


class TestCheckSettlementHealth:
    """Tests covering all trade_state × settlement_state combinations."""

    def test_healthy_terminated_settled(self, ds):
        result = check_settlement_health(ds, "trade_001")
        assert result["status"] == "HEALTHY"
        assert result["severity"] == "INFO"
        assert result["trade_state"] == "terminated"
        assert result["settlement_state"] == "settled"
        assert result["runbook_ref"] is None or "unknown" not in result["runbook_ref"]
        assert result.get("error") is not True

    def test_unhealthy_critical_defaulted(self, ds):
        result = check_settlement_health(ds, "trade_002")
        assert result["status"] == "UNHEALTHY"
        assert result["severity"] == "CRITICAL"
        assert result["runbook_ref"] == "runbook://settlement_default"

    def test_unhealthy_critical_counterparty_defaulted(self, ds):
        result = check_settlement_health(ds, "trade_003")
        assert result["status"] == "UNHEALTHY"
        assert result["severity"] == "CRITICAL"
        assert result["runbook_ref"] == "runbook://counterparty_default"

    def test_unhealthy_high_obligations_outstanding(self, ds):
        result = check_settlement_health(ds, "trade_004")
        assert result["status"] == "UNHEALTHY"
        assert result["severity"] == "HIGH"
        assert result["runbook_ref"] == "runbook://insufficient_liquidity"

    def test_pending_medium_current_obligations_met(self, ds):
        result = check_settlement_health(ds, "trade_005")
        assert result["status"] == "PENDING"
        assert result["severity"] == "MEDIUM"
        assert result["runbook_ref"] == "runbook://stale_trade"

    def test_pending_low_accepted_null(self, ds):
        result = check_settlement_health(ds, "trade_006")
        assert result["status"] == "PENDING"
        assert result["severity"] == "LOW"

    def test_unknown_unexpected_combo(self, ds):
        result = check_settlement_health(ds, "trade_007")
        assert result["status"] == "UNKNOWN"
        assert result["severity"] == "HIGH"
        assert result["runbook_ref"] == "runbook://unknown_state"

    def test_participant_code_derived(self, ds):
        """participant_code should be derived from the trade payload."""
        result = check_settlement_health(ds, "trade_001")
        assert result["participant_code"] == "PART_A"

    def test_participant_code_validated_match(self, ds):
        """Matching participant_code should succeed and enrich with balances."""
        result = check_settlement_health(ds, "trade_004", participant_code="PART_C")
        assert result.get("error") is not True
        assert result["participant_code"] == "PART_C"
        # Should have balance info appended to diagnosis
        assert "balance" in result["diagnosis"].lower() or "available" in result["diagnosis"].lower()

    def test_participant_code_validated_mismatch(self, ds):
        """Mismatched participant_code should return an error."""
        result = check_settlement_health(ds, "trade_001", participant_code="WRONG")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"
