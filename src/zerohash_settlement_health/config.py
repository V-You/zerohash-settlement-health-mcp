"""Configuration loader for the zerohash Settlement Health MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    data_source: str = "mock"  # "mock" or "live"

    # Zero Hash CERT API (V2)
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""
    api_base_url: str = "https://api.cert.zerohash.com"

    # Logging
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load settings from .env file and environment variables."""
    # Look for .env in project root (two levels up from this file)
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    return Settings(
        data_source=os.getenv("ZEROHASH_DATA_SOURCE", "mock").lower(),
        api_key=os.getenv("ZEROHASH_API_KEY", ""),
        api_secret=os.getenv("ZEROHASH_API_SECRET", ""),
        api_passphrase=os.getenv("ZEROHASH_API_PASSPHRASE", ""),
        api_base_url=os.getenv(
            "ZEROHASH_API_BASE_URL", "https://api.cert.zerohash.com"
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
