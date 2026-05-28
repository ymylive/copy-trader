"""Shop / pricing / purchase service."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import BadRequest, InsufficientFunds, NotFound
from app.db.models import (
    Coupon,
    ExchangeAccount,
    SubscriptionResource,
    User,
    WalletBalance,
    WalletTransaction,
)

log = logging.getLogger(__name__)


# Hard-coded SKU catalogue (matches Galaxy report) ─────────────────────


SKU_CATALOG: dict[str, dict] = {
    "order_slot": {
        "title": "下单名额（账户）",
        "description": "为单个交易所账户开启自动下单能力；按月订阅。",
        "price_usdt": 50.0,
        "duration_days": 30,
        "bind_account_required": True,
    },
    "follow_slot": {
        "title": "跟单名额（交易员）",
        "description": "为同一账户解锁额外一位跟单交易员位（可超出免费默认数）。",
        "price_usdt": 30.0,
        "duration_days": 30,
        "bind_account_required": False,
    },
    "lead_role": {
        "title": "带单员资格",
        "description": "开通成为系统带单员的资格，允许他人跟随你的信号。",
        "price_usdt": 100.0,
        "duration_days": 30,
        "bind_account_required": False,
    },
    "express_slot": {
        "title": "极速跟单升级",
        "description": "将账户升级到极速通道（<500ms 触达交易所）。",
        "price_usdt": 80.0,
        "duration_days": 30,
        "bind_account_required": True,
    },
}


def list_skus() -> List[dict]:
    return [
        {"sku": k, **v} for k, v in SKU_CATALOG.items()
    ]


def _get_sku(sku: str) -> dict:
    cfg = SKU_CATALOG.get(sku)
    if cfg is None:
        raise NotFound(f"unknown sku: {sku}", code="unknown_sku")
    return cfg


async def list_user_coupons(db: AsyncSession, user: User) -> List[Coupon]:
    rows = await db.execute(
        select(Coupon).where(Coupon.user_id == user.id, Coupon.used_at.is_(None))
    )
    return list(rows.scalars().all())


async def purchase(
    db: AsyncSession,
    user: User,
    *,
    sku: str,
    months: int = 1,
    bound_account_id: Optional[int] = None,
    coupon_code: Optional[str] = None,
    auto_renew: bool = False,
) -> tuple[SubscriptionResource, Decimal]:
    """Charge the user wallet, create SubscriptionResource, return (resource, balance_after)."""
    settings = get_settings()
    cfg = _get_sku(sku)

    # Validate bound account
    if cfg["bind_account_required"]:
        if bound_account_id is None:
            raise BadRequest("bound_account_id required for this sku", code="bound_account_required")
        acc = await db.get(ExchangeAccount, bound_account_id)
        if acc is None or acc.user_id != user.id:
            raise NotFound("bound account not found", code="account_not_found")

    base_price = Decimal(str(cfg["price_usdt"])) * Decimal(months)

    # Half-price for invited users on order_slot
    if sku == "order_slot" and user.referred_by is not None:
        base_price *= Decimal(str(settings.referral_half_price))

    # Coupon (85% off etc.)
    coupon: Optional[Coupon] = None
    if coupon_code:
        coupon = await db.scalar(
            select(Coupon).where(Coupon.code == coupon_code, Coupon.user_id == user.id)
        )
        if coupon is None:
            raise NotFound("coupon not found", code="coupon_not_found")
        if coupon.used_at is not None:
            raise BadRequest("coupon already used", code="coupon_used")
        if coupon.expires_at and coupon.expires_at < datetime.utcnow():
            raise BadRequest("coupon expired", code="coupon_expired")
        if coupon.sku_scope and sku not in coupon.sku_scope:
            raise BadRequest("coupon not applicable to this sku", code="coupon_scope")
        base_price *= Decimal(str(float(coupon.discount)))

    price = base_price.quantize(Decimal("0.00000001"))

    # Wallet check
    wallet = await db.scalar(
        select(WalletBalance).where(
            WalletBalance.user_id == user.id, WalletBalance.currency == "USDT"
        )
    )
    if wallet is None:
        wallet = WalletBalance(user_id=user.id, currency="USDT", amount=Decimal("0"))
        db.add(wallet)
        await db.flush()
    if wallet.amount < price:
        raise InsufficientFunds(
            f"need {price} USDT, have {wallet.amount}",
            code="insufficient_funds",
        )

    # Charge
    wallet.amount = wallet.amount - price
    db.add(
        WalletTransaction(
            user_id=user.id,
            type="consume",
            currency="USDT",
            amount=-price,
            ref_sku=sku,
            meta={"months": months, "coupon": coupon_code},
        )
    )

    # Mark coupon used
    if coupon is not None:
        coupon.used_at = datetime.utcnow()

    # Create resource
    duration_days = cfg["duration_days"] * months
    resource = SubscriptionResource(
        user_id=user.id,
        sku=sku,
        bound_account_id=bound_account_id,
        purchase_time=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=duration_days),
        auto_renew=auto_renew,
        coupon_id=coupon.id if coupon else None,
        paid_amount=price,
    )
    db.add(resource)
    await db.flush()

    # If bound to an account, push the service_expires_at
    if bound_account_id and sku in ("order_slot", "express_slot"):
        acc = await db.get(ExchangeAccount, bound_account_id)
        if acc is not None:
            new_expiry = resource.expires_at
            if acc.service_expires_at is None or acc.service_expires_at < datetime.utcnow():
                acc.service_expires_at = new_expiry
            else:
                acc.service_expires_at = acc.service_expires_at + timedelta(days=duration_days)
            if sku == "express_slot":
                acc.tier = "express"

    log.info(
        "shop.purchase user_id=%s sku=%s months=%s paid=%s coupon=%s",
        user.id, sku, months, price, coupon_code,
    )
    return resource, wallet.amount
