"""Pydantic models for market price data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarketPrice(BaseModel):
    """Current market price for a single asset."""

    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    price_usd: str = Field(..., description="Current price in USD")
    change_24h_pct: Optional[str] = Field(
        None, description="24-hour price change as percentage"
    )
    last_updated: Optional[datetime] = Field(
        None, description="Timestamp of the last price update from source"
    )


class MarketPriceResult(BaseModel):
    """Result of a market price lookup."""

    prices: list[MarketPrice] = Field(default_factory=list)
    vs_currency: str = Field(default="usd")
    source: str = Field(default="coingecko")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
