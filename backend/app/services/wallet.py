"""Wallet operations."""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Sequence, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, InsufficientFunds, NotFound
from app.db.models import (
    SubscriptionResource,
    User,
    WalletBalance,
    WalletTransaction,
)

log = logging.getLogger(__name__)


async def get_balances(db: AsyncSession, user: User) -> Sequence[WalletBalance]:
    rows = await db.execute(
        select(WalletBalance).where(WalletBalance.user_id == user.id)
    )
    return rows.scalars().all()


async def list_resources(db: AsyncSession, user: User) -> Sequence[SubscriptionResource]:
    rows = await db.execute(
        select(SubscriptionResource)
        .where(SubscriptionResource.user_id == user.id)
        .order_by(desc(SubscriptionResource.expires_at))
    )
    return rows.scalars().all()


async def set_auto_renew(
    db: AsyncSession, user: User, resource_id: int, *, auto_renew: bool
) -> SubscriptionResource:
    res = await db.get(SubscriptionResource, resource_id)
    if res is None or res.user_id != user.id:
        raise NotFound("resource not found", code="resource_not_found")
    res.auto_renew = auto_renew
    return res


async def list_transactions(
    db: AsyncSession, user: User, *, page: int = 1, page_size: int = 50
) -> Tuple[Sequence[WalletTransaction], int]:
    total_q = select(func.count()).select_from(WalletTransaction).where(
        WalletTransaction.user_id == user.id
    )
    total = (await db.execute(total_q)).scalar_one()
    rows = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == user.id)
        .order_by(desc(WalletTransaction.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return rows.scalars().all(), int(total)


async def deposit(
    db: AsyncSession, user: User, *, amount: Decimal, currency: str = "USDT",
    ref: str | None = None, meta: dict | None = None,
) -> WalletBalance:
    """Credit user wallet (used by deposit/refund/referral)."""
    if amount <= 0:
        raise BadRequest("amount must be positive", code="bad_amount")
    wallet = await db.scalar(
        select(WalletBalance).where(
            WalletBalance.user_id == user.id, WalletBalance.currency == currency
        )
    )
    if wallet is None:
        wallet = WalletBalance(user_id=user.id, currency=currency, amount=Decimal("0"))
        db.add(wallet)
        await db.flush()
    wallet.amount = wallet.amount + amount
    db.add(
        WalletTransaction(
            user_id=user.id, type="deposit", currency=currency,
            amount=amount, ref_sku=ref, meta=meta or {},
        )
    )
    log.info("wallet.deposit user_id=%s amount=%s", user.id, amount)
    return wallet


async def withdraw(
    db: AsyncSession, user: User, *, amount: Decimal, currency: str, chain: str, address: str,
) -> WalletBalance:
    if amount <= 0:
        raise BadRequest("amount must be positive", code="bad_amount")
    wallet = await db.scalar(
        select(WalletBalance).where(
            WalletBalance.user_id == user.id, WalletBalance.currency == currency
        )
    )
    if wallet is None or wallet.amount < amount:
        raise InsufficientFunds("insufficient balance", code="insufficient_funds")
    wallet.amount = wallet.amount - amount
    db.add(
        WalletTransaction(
            user_id=user.id, type="withdraw", currency=currency,
            amount=-amount, ref_sku=None,
            meta={"chain": chain, "address": address, "status": "pending"},
        )
    )
    log.info("wallet.withdraw user_id=%s amount=%s addr=%s", user.id, amount, address)
    return wallet
