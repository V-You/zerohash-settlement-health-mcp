"""Data source factory."""

from __future__ import annotations

from zerohash_settlement_health.config import Settings
from zerohash_settlement_health.data_source.base import DataSource
from zerohash_settlement_health.data_source.live import LiveDataSource
from zerohash_settlement_health.data_source.mock import MockDataSource


def create_data_source(settings: Settings) -> DataSource:
    """Create the appropriate data source based on configuration.

    Args:
        settings: Application settings.

    Returns:
        A DataSource instance (MockDataSource or LiveDataSource).
    """
    if settings.data_source == "live":
        return LiveDataSource(
            api_key=settings.api_key,
            api_secret=settings.api_secret,
            api_passphrase=settings.api_passphrase,
            base_url=settings.api_base_url,
        )
    return MockDataSource()


__all__ = ["DataSource", "MockDataSource", "LiveDataSource", "create_data_source"]
