"""Referral / invite endpoints."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientFunds
from app.deps import get_current_user, get_db
from app.db.models import ReferralRecord, User, WalletBalance, WalletTransaction
from app.schemas.common import MessageOut
from app.schemas.invite import (
    CommissionWithdrawIn,
    InviteSummaryOut,
    ReferralRecordOut,
)

router = APIRouter()


@router.get("/me", response_model=InviteSummaryOut)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InviteSummaryOut:
    total = (
        await db.execute(
            select(func.count())
            .select_from(ReferralRecord)
            .where(ReferralRecord.inviter_id == user.id)
        )
    ).scalar_one()
    total_commission = (
        await db.execute(
            select(func.coalesce(func.sum(ReferralRecord.commission), 0))
            .where(ReferralRecord.inviter_id == user.id, ReferralRecord.status == "paid")
        )
    ).scalar_one()
    pending_commission = (
        await db.execute(
            select(func.coalesce(func.sum(ReferralRecord.commission), 0))
            .where(ReferralRecord.inviter_id == user.id, ReferralRecord.status == "pending")
        )
    ).scalar_one()
    return InviteSummaryOut(
        invite_code=user.invite_code or "",
        referral_rate=float(user.referral_rate),
        total_invitees=int(total),
        total_commission=float(total_commission),
        pending_commission=float(pending_commission),
    )


@router.get("/records", response_model=List[ReferralRecordOut])
async def records(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReferralRecordOut]:
    rows = await db.execute(
        select(ReferralRecord, User.username)
        .join(User, User.id == ReferralRecord.invitee_id)
        .where(ReferralRecord.inviter_id == user.id)
        .order_by(ReferralRecord.registered_at.desc())
    )
    out: List[ReferralRecordOut] = []
    for rec, invitee_name in rows.all():
        out.append(
            ReferralRecordOut(
                id=rec.id,
                invitee_id=rec.invitee_id,
                invitee_username=invitee_name,
                registered_at=rec.registered_at,
                paid_amount=float(rec.paid_amount),
                commission=float(rec.commission),
                status=rec.status,
            )
        )
    return out


@router.post("/withdraw", response_model=MessageOut)
async def withdraw(
    payload: CommissionWithdrawIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    """Move accumulated commission into wallet, then schedule USDT withdraw."""
    amt = Decimal(str(payload.amount))
    pending_commission = (
        await db.execute(
            select(func.coalesce(func.sum(ReferralRecord.commission), 0))
            .where(ReferralRecord.inviter_id == user.id, ReferralRecord.status == "paid")
        )
    ).scalar_one()
    if Decimal(str(pending_commission)) < amt:
        raise InsufficientFunds("commission balance too low", code="insufficient_commission")
    wallet = await db.scalar(
        select(WalletBalance).where(
            WalletBalance.user_id == user.id, WalletBalance.currency == "USDT"
        )
    )
    if wallet is None:
        wallet = WalletBalance(user_id=user.id, currency="USDT", amount=Decimal("0"))
        db.add(wallet)
        await db.flush()
    wallet.amount = wallet.amount + amt
    db.add(
        WalletTransaction(
            user_id=user.id, type="referral", currency="USDT", amount=amt,
            ref_sku=None, meta={"source": "commission_withdraw"},
        )
    )
    return MessageOut(message="commission_moved_to_wallet", data={"amount": str(amt)})
