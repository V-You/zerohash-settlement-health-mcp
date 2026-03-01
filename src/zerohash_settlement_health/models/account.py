"""Pydantic models for Zero Hash account data."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Account(BaseModel):
    """Represents a single account balance entry."""

    asset: str = Field(..., description="Asset symbol (e.g., BTC, USD)")
    balance: str = Field(..., description="Total balance")
    available_balance: str = Field(..., description="Available (non-held) balance")
    account_group: str = Field(default="", description="Account group identifier")


class AccountBalanceResult(BaseModel):
    """Result of an account balance check."""

    participant_code: str
    accounts: list[Account] = Field(default_factory=list)
