"""Shop / SKU / coupon schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.common import APIModel


class SkuOut(APIModel):
    sku: str
    title: str
    description: str
    price_usdt: float
    duration_days: int
    bind_account_required: bool = False


class PurchaseIn(APIModel):
    sku: str
    months: int = Field(default=1, ge=1, le=24)
    bound_account_id: Optional[int] = None
    coupon_code: Optional[str] = None
    auto_renew: bool = False


class PurchaseOut(APIModel):
    resource_id: int
    sku: str
    bound_account_id: Optional[int] = None
    expires_at: datetime
    paid_amount: float
    wallet_balance_after: float


class CouponOut(APIModel):
    id: int
    code: Optional[str] = None
    discount: float
    sku_scope: List[str] = []
    expires_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    created_at: datetime
