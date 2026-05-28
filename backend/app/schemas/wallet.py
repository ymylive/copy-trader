"""Wallet schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import APIModel


class BalanceOut(APIModel):
    currency: str
    amount: float


class WalletSummaryOut(APIModel):
    balances: List[BalanceOut]
    total_usdt: float


class ResourceOut(APIModel):
    id: int
    sku: str
    bound_account_id: Optional[int] = None
    purchase_time: datetime
    expires_at: datetime
    auto_renew: bool
    paid_amount: float


class TransactionOut(APIModel):
    id: int
    type: str
    currency: str
    amount: float
    ref_sku: Optional[str] = None
    meta: Dict[str, Any] = {}
    created_at: datetime


class RechargeIn(APIModel):
    currency: str = Field(default="USDT", pattern=r"^(USDT|USDC)$")
    chain: str = Field(default="TRC20", pattern=r"^(TRC20|ERC20|BEP20)$")


class RechargeOut(APIModel):
    address: str
    currency: str
    chain: str
    memo: Optional[str] = None
    qr_code_url: Optional[str] = None


class WithdrawIn(APIModel):
    currency: str = "USDT"
    chain: str = "TRC20"
    address: str
    amount: float = Field(gt=0)
