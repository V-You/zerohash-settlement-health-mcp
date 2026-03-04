"""Tests for get_market_prices tool and market_data module."""

import importlib
import sys

import pytest

# Import the actual module (not the re-exported function from __init__.py)
_gmp_module = importlib.import_module("zerohash_settlement_health.tools.get_market_prices")

from zerohash_settlement_health.models.market import MarketPrice
from zerohash_settlement_health.tools.get_market_prices import get_market_prices


# --- Fixtures ---

MOCK_COINGECKO_RESPONSE = {
    "bitcoin": {
        "usd": 67234.5,
        "usd_24h_change": -2.31,
        "last_updated_at": 1772712000,
    },
    "ethereum": {
        "usd": 3456.78,
        "usd_24h_change": 1.05,
        "last_updated_at": 1772712000,
    },
    "solana": {
        "usd": 142.30,
        "usd_24h_change": -0.45,
        "last_updated_at": 1772712000,
    },
}


def _mock_fetch_prices(response_data):
    """Create a mock fetch_prices that returns data derived from a CoinGecko-like response."""
    from zerohash_settlement_health.market_data import SYMBOL_TO_COINGECKO_ID
    from datetime import datetime, timezone

    # Build reverse mapping
    id_to_symbol = {v: k for k, v in SYMBOL_TO_COINGECKO_ID.items()}

    def mock(symbols, vs_currency="usd", error_log_enabled=False):
        result = {}
        for sym in symbols:
            upper = sym.upper()
            cg_id = SYMBOL_TO_COINGECKO_ID.get(upper)
            if cg_id and cg_id in response_data:
                data = response_data[cg_id]
                price = data.get(vs_currency)
                if price is not None:
                    change = data.get(f"{vs_currency}_24h_change")
                    ts = data.get("last_updated_at")
                    result[upper] = MarketPrice(
                        asset=upper,
                        price_usd=str(price),
                        change_24h_pct=f"{change:.2f}" if change is not None else None,
                        last_updated=datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None,
                    )
        return result

    return mock


class TestGetMarketPrices:
    """Tests for the get_market_prices tool function."""

    def test_success_default_assets(self, monkeypatch):
        """Default BTC,ETH,SOL returns all 3 prices."""
        monkeypatch.setattr(
            _gmp_module, "fetch_prices",
            _mock_fetch_prices(MOCK_COINGECKO_RESPONSE),
        )
        result = get_market_prices()
        assert result.get("error") is not True
        assert len(result["prices"]) == 3
        assert result["vs_currency"] == "usd"
        assert result["source"] == "coingecko"
        symbols = {p["asset"] for p in result["prices"]}
        assert symbols == {"BTC", "ETH", "SOL"}

    def test_success_single_asset(self, monkeypatch):
        """Single asset returns 1 price."""
        monkeypatch.setattr(
            _gmp_module, "fetch_prices",
            _mock_fetch_prices(MOCK_COINGECKO_RESPONSE),
        )
        result = get_market_prices(assets="BTC")
        assert result.get("error") is not True
        assert len(result["prices"]) == 1
        assert result["prices"][0]["asset"] == "BTC"
        assert result["prices"][0]["price_usd"] == "67234.5"

    def test_includes_24h_change(self, monkeypatch):
        monkeypatch.setattr(
            _gmp_module, "fetch_prices",
            _mock_fetch_prices(MOCK_COINGECKO_RESPONSE),
        )
        result = get_market_prices(assets="ETH")
        assert result["prices"][0]["change_24h_pct"] == "1.05"

    def test_partial_unknown_symbols(self, monkeypatch):
        """Unknown symbols are skipped, known ones returned."""
        monkeypatch.setattr(
            _gmp_module, "fetch_prices",
            _mock_fetch_prices(MOCK_COINGECKO_RESPONSE),
        )
        result = get_market_prices(assets="BTC,UNKNOWN_XYZ")
        assert result.get("error") is not True
        assert len(result["prices"]) == 1
        assert result["prices"][0]["asset"] == "BTC"

    def test_all_unknown_symbols(self, monkeypatch):
        """All unknown symbols returns error."""
        monkeypatch.setattr(_gmp_module, "fetch_prices", lambda *a, **kw: {})
        result = get_market_prices(assets="UNKNOWN1,UNKNOWN2")
        assert result["error"] is True
        assert result["error_code"] == "EXTERNAL_API_ERROR"

    def test_empty_input(self):
        """Empty assets string returns error."""
        result = get_market_prices(assets="")
        assert result["error"] is True
        assert result["error_code"] == "INVALID_INPUT"

    def test_whitespace_handling(self, monkeypatch):
        """Whitespace around symbols is stripped."""
        monkeypatch.setattr(
            _gmp_module, "fetch_prices",
            _mock_fetch_prices(MOCK_COINGECKO_RESPONSE),
        )
        result = get_market_prices(assets=" BTC , ETH ")
        assert result.get("error") is not True
        assert len(result["prices"]) == 2

    def test_api_failure(self, monkeypatch):
        """API failure (returns empty dict) gives error response."""
        monkeypatch.setattr(_gmp_module, "fetch_prices", lambda *a, **kw: {})
        result = get_market_prices(assets="BTC,ETH,SOL")
        assert result["error"] is True
        assert result["error_code"] == "EXTERNAL_API_ERROR"

    def test_timestamp_present(self, monkeypatch):
        monkeypatch.setattr(
            _gmp_module, "fetch_prices",
            _mock_fetch_prices(MOCK_COINGECKO_RESPONSE),
        )
        result = get_market_prices()
        assert "timestamp" in result


class TestErrorLogging:
    """Tests for market_errors.log opt-in logging."""

    def test_error_log_written_when_enabled(self, monkeypatch, tmp_path):
        """When error_log_enabled=True, errors are written to log file."""
        import zerohash_settlement_health.market_data as md

        log_file = tmp_path / "market_errors.log"
        monkeypatch.setattr(md, "_LOG_FILE", log_file)

        # Simulate a call that triggers an error
        import httpx
        monkeypatch.setattr(
            md.httpx, "Client",
            _FakeClientFactory(httpx.TimeoutException("test timeout")),
        )

        result = md.fetch_prices(["BTC"], error_log_enabled=True)
        assert result == {}
        assert log_file.exists()
        content = log_file.read_text()
        assert "type=timeout" in content
        assert "source=coingecko" in content

    def test_error_log_not_written_when_disabled(self, monkeypatch, tmp_path):
        """When error_log_enabled=False, no log file is written."""
        import zerohash_settlement_health.market_data as md

        log_file = tmp_path / "market_errors.log"
        monkeypatch.setattr(md, "_LOG_FILE", log_file)

        import httpx
        monkeypatch.setattr(
            md.httpx, "Client",
            _FakeClientFactory(httpx.TimeoutException("test timeout")),
        )

        result = md.fetch_prices(["BTC"], error_log_enabled=False)
        assert result == {}
        assert not log_file.exists()

    def test_error_log_appends(self, monkeypatch, tmp_path):
        """Multiple errors are appended, not overwritten."""
        import zerohash_settlement_health.market_data as md

        log_file = tmp_path / "market_errors.log"
        monkeypatch.setattr(md, "_LOG_FILE", log_file)

        import httpx
        monkeypatch.setattr(
            md.httpx, "Client",
            _FakeClientFactory(httpx.TimeoutException("timeout1")),
        )

        md.fetch_prices(["BTC"], error_log_enabled=True)
        md.fetch_prices(["ETH"], error_log_enabled=True)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2


class _FakeResponse:
    """Fake httpx response for testing error paths."""

    def __init__(self, exc):
        self._exc = exc

    def raise_for_status(self):
        pass

    def json(self):
        return {}


class _FakeClient:
    """Fake httpx.Client that raises a given exception on .get()."""

    def __init__(self, exc):
        self._exc = exc

    def get(self, *args, **kwargs):
        raise self._exc

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _FakeClientFactory:
    """Returns a _FakeClient when called (mimics httpx.Client constructor)."""

    def __init__(self, exc):
        self._exc = exc

    def __call__(self, **kwargs):
        return _FakeClient(self._exc)
