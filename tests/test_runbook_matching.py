"""Tests for runbook loading and matching."""

import pytest

from zerohash_settlement_health.runbooks import (
    get_all_runbooks,
    get_runbook,
    match_runbook,
    runbook_to_text,
)


class TestRunbookLoading:
    def test_all_runbooks_loaded(self):
        runbooks = get_all_runbooks()
        assert len(runbooks) == 5
        expected_ids = {
            "insufficient_liquidity",
            "settlement_default",
            "counterparty_default",
            "stale_trade",
            "unknown_state",
        }
        assert set(runbooks.keys()) == expected_ids

    def test_get_specific_runbook(self):
        rb = get_runbook("insufficient_liquidity")
        assert rb is not None
        assert rb["title"] == "Insufficient Liquidity for Settlement"
        assert rb["severity"] == "HIGH"

    def test_get_nonexistent_runbook(self):
        assert get_runbook("does_not_exist") is None


class TestRunbookMatching:
    def test_match_active_obligations_outstanding(self):
        rb = match_runbook("active", "obligations_outstanding")
        assert rb is not None
        assert rb["id"] == "insufficient_liquidity"

    def test_match_terminated_defaulted(self):
        rb = match_runbook("terminated", "defaulted")
        assert rb is not None
        assert rb["id"] == "settlement_default"

    def test_match_terminated_counterparty_defaulted(self):
        rb = match_runbook("terminated", "counterparty_defaulted")
        assert rb is not None
        assert rb["id"] == "counterparty_default"

    def test_match_active_current_obligations_met(self):
        rb = match_runbook("active", "current_obligations_met")
        assert rb is not None
        assert rb["id"] == "stale_trade"

    def test_match_unknown_falls_back(self):
        """Unrecognized state combo should fall back to unknown_state."""
        rb = match_runbook("terminated", "obligations_outstanding")
        assert rb is not None
        assert rb["id"] == "unknown_state"

    def test_match_with_none_settlement_state(self):
        """accepted + None should not match a specific runbook (no trigger for it)."""
        rb = match_runbook("accepted", None)
        # Falls back to unknown_state since there's no trigger for accepted/null
        assert rb is not None


class TestRunbookFormatting:
    def test_runbook_to_text(self):
        rb = get_runbook("insufficient_liquidity")
        text = runbook_to_text(rb)
        assert "Insufficient Liquidity" in text
        assert "Diagnosis Steps" in text
        assert "Remediation" in text
        assert "API References" in text
