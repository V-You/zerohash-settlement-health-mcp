"""Tests for the diagnose_errors tool and supporting modules."""

import os
import tempfile

import pytest

from zerohash_settlement_health.log_parser import (
    build_provider_impact,
    group_into_incidents,
    parse_log_lines,
)
from zerohash_settlement_health.runbooks import match_error_runbook
from zerohash_settlement_health.tools.diagnose_errors import diagnose_errors


# ---------------------------------------------------------------------------
# Sample log data
# ---------------------------------------------------------------------------

SAMPLE_503_LOG = """\
[14:38:01] INFO: Received POST /liquidity/rfq from Client_882 (IP: 192.168.1.1)
[14:38:01] ERROR: Upstream liquidity provider 'PrimeX' timed out after 5000ms.
[14:38:01] DEBUG: Returning 503 Service Unavailable to Client_882.
"""

SAMPLE_400_LOG = """\
[14:42:10] INFO: Received POST /withdrawals from Client_882 (IP: 192.168.1.1)
[14:42:10] WARN: Validation failed for field 'asset_amount'. Expected: DECIMAL, Received: STRING ("ten_btc").
[14:42:10] DEBUG: Returning 400 Bad Request - {"message": "Invalid data"} to Client_882.
"""

FULL_SAMPLE_LOG = SAMPLE_503_LOG + "\n" + SAMPLE_400_LOG

MULTI_CLIENT_503_LOG = """\
[14:38:01] INFO: Received POST /liquidity/rfq from Client_882 (IP: 192.168.1.1)
[14:38:01] ERROR: Upstream liquidity provider 'PrimeX' timed out after 5000ms.
[14:38:01] DEBUG: Returning 503 Service Unavailable to Client_882.
[14:39:05] INFO: Received POST /liquidity/rfq from Client_999 (IP: 10.0.0.1)
[14:39:05] ERROR: Upstream liquidity provider 'PrimeX' timed out after 5000ms.
[14:39:05] DEBUG: Returning 503 Service Unavailable to Client_999.
"""


# ---------------------------------------------------------------------------
# Test 1: Parse 503 upstream timeout
# ---------------------------------------------------------------------------

class TestParse503:
    def test_503_incident_classification(self):
        result = diagnose_errors(log_text=SAMPLE_503_LOG)
        assert "error" not in result
        assert len(result["incidents"]) == 1

        inc = result["incidents"][0]
        assert inc["category"] == "SERVER_SIDE"
        assert inc["upstream_provider"] == "PrimeX"
        assert inc["runbook_ref"] == "runbook://upstream_timeout"
        assert inc["draft_response"] is not None
        assert inc["status_code"] == 503
        assert inc["client_id"] == "Client_882"


# ---------------------------------------------------------------------------
# Test 2: Parse 400 invalid input
# ---------------------------------------------------------------------------

class TestParse400:
    def test_400_incident_classification(self):
        result = diagnose_errors(log_text=SAMPLE_400_LOG)
        assert "error" not in result
        assert len(result["incidents"]) == 1

        inc = result["incidents"][0]
        assert inc["category"] == "CLIENT_SIDE"
        assert inc["upstream_provider"] is None
        assert inc["runbook_ref"] == "runbook://invalid_input"
        assert inc["status_code"] == 400


# ---------------------------------------------------------------------------
# Test 3: Full sample log — two incidents
# ---------------------------------------------------------------------------

class TestFullSample:
    def test_two_incidents_with_provider_impact(self):
        result = diagnose_errors(log_text=FULL_SAMPLE_LOG)
        assert len(result["incidents"]) == 2

        # Provider impact
        assert "PrimeX" in result["provider_impact"]
        assert result["provider_impact"]["PrimeX"]["incident_count"] == 1

        # Summary
        assert result["summary"]["server_side"] == 1
        assert result["summary"]["client_side"] == 1
        assert result["summary"]["total_incidents"] == 2


# ---------------------------------------------------------------------------
# Test 4: Both log_text and file_path provided
# ---------------------------------------------------------------------------

class TestBothInputs:
    def test_merged_inputs(self, tmp_path, monkeypatch):
        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_503_LOG)
        monkeypatch.chdir(tmp_path)

        result = diagnose_errors(
            log_text=SAMPLE_400_LOG,
            file_path="test.log",
        )
        assert len(result["incidents"]) == 2


# ---------------------------------------------------------------------------
# Test 5: Empty log text — zero incidents
# ---------------------------------------------------------------------------

class TestEmptyLog:
    def test_empty_log_returns_zero_incidents(self):
        result = diagnose_errors(log_text="no parseable lines here")
        assert "error" not in result
        assert result["summary"]["total_incidents"] == 0
        assert result["incidents"] == []
        assert result["provider_impact"] == {}


# ---------------------------------------------------------------------------
# Test 6: Neither input provided
# ---------------------------------------------------------------------------

class TestNoInput:
    def test_no_input_returns_error(self):
        result = diagnose_errors()
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"

    def test_empty_strings_returns_error(self):
        result = diagnose_errors(log_text="", file_path="")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"


# ---------------------------------------------------------------------------
# Test 7: Nonexistent file_path
# ---------------------------------------------------------------------------

class TestFileNotFound:
    def test_nonexistent_file(self):
        result = diagnose_errors(file_path="nonexistent.log")
        assert result["error"] is True
        assert result["error_code"] == "FILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# Test 8: Unknown status code
# ---------------------------------------------------------------------------

class TestUnknownStatusCode:
    def test_unknown_code_418(self):
        log = """\
[10:00:00] INFO: Received GET /teapot from Client_001 (IP: 1.2.3.4)
[10:00:00] DEBUG: Returning 418 I'm a teapot to Client_001.
"""
        result = diagnose_errors(log_text=log)
        assert len(result["incidents"]) == 1

        inc = result["incidents"][0]
        assert inc["category"] == "CLIENT_SIDE"  # 4xx range fallback
        assert inc["runbook_ref"] is None
        assert inc["draft_response"] is None


# ---------------------------------------------------------------------------
# Test 9: Multiple clients, same provider
# ---------------------------------------------------------------------------

class TestMultiClientProvider:
    def test_provider_impact_lists_both_clients(self):
        result = diagnose_errors(log_text=MULTI_CLIENT_503_LOG)
        assert "PrimeX" in result["provider_impact"]
        impact = result["provider_impact"]["PrimeX"]
        assert set(impact["affected_clients"]) == {"Client_882", "Client_999"}
        assert impact["incident_count"] == 2


# ---------------------------------------------------------------------------
# Test 10: Runbook YAML loaded — match_error_runbook
# ---------------------------------------------------------------------------

class TestRunbookMatching:
    def test_match_503(self):
        rb = match_error_runbook(503)
        assert rb is not None
        assert rb["id"] == "upstream_timeout"

    def test_match_400(self):
        rb = match_error_runbook(400)
        assert rb is not None
        assert rb["id"] == "invalid_input"

    def test_match_500(self):
        rb = match_error_runbook(500)
        assert rb is not None
        assert rb["id"] == "internal_error"

    def test_match_429(self):
        rb = match_error_runbook(429)
        assert rb is not None
        assert rb["id"] == "rate_limit"

    def test_no_match_for_200(self):
        rb = match_error_runbook(200)
        assert rb is None


# ---------------------------------------------------------------------------
# Test 11: Path traversal rejected
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_dotdot_traversal_rejected(self):
        result = diagnose_errors(file_path="../../etc/passwd")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"

    def test_dotdot_in_middle_rejected(self):
        result = diagnose_errors(file_path="logs/../../../etc/shadow")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"


# ---------------------------------------------------------------------------
# Test 12: Absolute path rejected
# ---------------------------------------------------------------------------

class TestAbsolutePath:
    def test_absolute_path_rejected(self):
        result = diagnose_errors(file_path="/var/log/syslog")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"


# ---------------------------------------------------------------------------
# Test 13: Multi-code runbook (401 and 403 -> auth_failure)
# ---------------------------------------------------------------------------

class TestMultiCodeRunbook:
    def test_401_matches_auth_failure(self):
        rb = match_error_runbook(401)
        assert rb is not None
        assert rb["id"] == "auth_failure"

    def test_403_matches_auth_failure(self):
        rb = match_error_runbook(403)
        assert rb is not None
        assert rb["id"] == "auth_failure"


# ---------------------------------------------------------------------------
# Test: observed_window in summary
# ---------------------------------------------------------------------------

class TestObservedWindow:
    def test_observed_window_present(self):
        result = diagnose_errors(log_text=FULL_SAMPLE_LOG)
        window = result["summary"]["observed_window"]
        assert window is not None
        assert window["first"] == "14:38:01"
        assert window["last"] == "14:42:10"

    def test_observed_window_none_for_empty(self):
        result = diagnose_errors(log_text="nothing here")
        assert result["summary"]["observed_window"] is None


# ---------------------------------------------------------------------------
# Test: Log parser unit tests
# ---------------------------------------------------------------------------

class TestLogParser:
    def test_parse_extracts_fields(self):
        entries = parse_log_lines(SAMPLE_503_LOG)
        assert len(entries) == 3

        info = entries[0]
        assert info.timestamp == "14:38:01"
        assert info.level == "INFO"
        assert info.client_id == "Client_882"
        assert info.endpoint == "POST /liquidity/rfq"

        error = entries[1]
        assert error.upstream_provider == "PrimeX"

        debug = entries[2]
        assert debug.status_code == 503

    def test_non_matching_lines_skipped(self):
        text = "This is not a log line\n[14:00:00] INFO: Valid line"
        entries = parse_log_lines(text)
        assert len(entries) == 1

    def test_grouping_by_client_endpoint(self):
        entries = parse_log_lines(FULL_SAMPLE_LOG)
        groups = group_into_incidents(entries)
        assert len(groups) == 2


# ---------------------------------------------------------------------------
# Test: Bad file extension rejected
# ---------------------------------------------------------------------------

class TestBadExtension:
    def test_py_extension_rejected(self):
        result = diagnose_errors(file_path="script.py")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"

    def test_yaml_extension_rejected(self):
        result = diagnose_errors(file_path="config.yaml")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"
