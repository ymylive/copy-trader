"""Shop / SKU / coupon endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.shop import CouponOut, PurchaseIn, PurchaseOut, SkuOut
from app.services import shop as shop_svc

router = APIRouter()


@router.get("/skus", response_model=List[SkuOut])
async def list_skus() -> List[SkuOut]:
    return [SkuOut(**s) for s in shop_svc.list_skus()]


@router.post("/purchase", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
async def purchase(
    payload: PurchaseIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PurchaseOut:
    resource, balance_after = await shop_svc.purchase(
        db, user,
        sku=payload.sku,
        months=payload.months,
        bound_account_id=payload.bound_account_id,
        coupon_code=payload.coupon_code,
        auto_renew=payload.auto_renew,
    )
    return PurchaseOut(
        resource_id=resource.id,
        sku=resource.sku,
        bound_account_id=resource.bound_account_id,
        expires_at=resource.expires_at,
        paid_amount=float(resource.paid_amount),
        wallet_balance_after=float(balance_after),
    )


@router.get("/coupons", response_model=List[CouponOut])
async def list_coupons(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CouponOut]:
    items = await shop_svc.list_user_coupons(db, user)
    return [
        CouponOut(
            id=c.id,
            code=c.code,
            discount=float(c.discount),
            sku_scope=list(c.sku_scope or []),
            expires_at=c.expires_at,
            used_at=c.used_at,
            created_at=c.created_at,
        )
        for c in items
    ]
