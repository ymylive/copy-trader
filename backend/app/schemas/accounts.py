"""Exchange account schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from app.schemas.common import APIModel


class ExchangeAccountCreate(APIModel):
    alias: str = Field(min_length=1, max_length=64)
    tier: str = Field(default="standard", pattern=r"^(standard|express)$")
    exchange: str = Field(pattern=r"^(binance|okx|gate|bitget|hyperliquid)$")
    leverage_default: int = Field(default=10, ge=1, le=125)


class ExchangeAccountUpdate(APIModel):
    alias: Optional[str] = Field(default=None, min_length=1, max_length=64)
    leverage_default: Optional[int] = Field(default=None, ge=1, le=125)


class APIKeyIn(APIModel):
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    passphrase: Optional[str] = None
    uid: Optional[str] = None


class ExchangeAccountOut(APIModel):
    id: int
    user_id: int
    alias: str
    tier: str
    exchange: str
    uid: Optional[str] = None
    leverage_default: int
    status: str
    egress_ips: List[str] = []
    activated_at: Optional[datetime] = None
    service_expires_at: Optional[datetime] = None
    has_api_key: bool = False
    created_at: datetime


class BalanceOut(APIModel):
    account_id: int
    currency: str = "USDT"
    total_balance: float
    available_balance: float
    unrealized_pnl: float
    updated_at: datetime


class PositionOut(APIModel):
    symbol: str
    side: str
    qty: float
    entry_px: Optional[float] = None
    lev: Optional[float] = None
    margin: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    ts: datetime


class NavPointOut(APIModel):
    ts: datetime
    total_balance: float
    realized_pnl: float
    unrealized_pnl: float
