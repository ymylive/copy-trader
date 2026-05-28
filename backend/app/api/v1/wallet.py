"""Wallet endpoints."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.common import MessageOut, Page
from app.schemas.wallet import (
    BalanceOut,
    RechargeIn,
    RechargeOut,
    ResourceOut,
    TransactionOut,
    WalletSummaryOut,
    WithdrawIn,
)
from app.services import wallet as wallet_svc

router = APIRouter()


@router.get("/balance", response_model=WalletSummaryOut)
async def get_balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WalletSummaryOut:
    balances = await wallet_svc.get_balances(db, user)
    out = [BalanceOut(currency=b.currency, amount=float(b.amount)) for b in balances]
    total_usdt = sum(b.amount for b in out if b.currency == "USDT")
    return WalletSummaryOut(balances=out, total_usdt=float(total_usdt))


@router.get("/resources", response_model=List[ResourceOut])
async def list_resources(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ResourceOut]:
    res = await wallet_svc.list_resources(db, user)
    return [
        ResourceOut(
            id=r.id,
            sku=r.sku,
            bound_account_id=r.bound_account_id,
            purchase_time=r.purchase_time,
            expires_at=r.expires_at,
            auto_renew=r.auto_renew,
            paid_amount=float(r.paid_amount),
        )
        for r in res
    ]


@router.post("/resources/{resource_id}/auto-renew", response_model=ResourceOut)
async def toggle_auto_renew(
    resource_id: int,
    auto_renew: bool = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResourceOut:
    r = await wallet_svc.set_auto_renew(db, user, resource_id, auto_renew=auto_renew)
    return ResourceOut(
        id=r.id,
        sku=r.sku,
        bound_account_id=r.bound_account_id,
        purchase_time=r.purchase_time,
        expires_at=r.expires_at,
        auto_renew=r.auto_renew,
        paid_amount=float(r.paid_amount),
    )


@router.post("/resources/{resource_id}/renew", response_model=MessageOut)
async def renew_resource(
    resource_id: int,
    months: int = Query(default=1, ge=1, le=24),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    """Renew a subscription: shorthand for shop.purchase with same sku."""
    from app.services import shop as shop_svc
    from app.db.models import SubscriptionResource

    res = await db.get(SubscriptionResource, resource_id)
    if res is None or res.user_id != user.id:
        from app.core.exceptions import NotFound
        raise NotFound("resource not found", code="resource_not_found")
    new_res, _ = await shop_svc.purchase(
        db, user,
        sku=res.sku,
        months=months,
        bound_account_id=res.bound_account_id,
        auto_renew=res.auto_renew,
    )
    return MessageOut(message="renewed", data={"new_resource_id": new_res.id})


@router.get("/transactions", response_model=Page[TransactionOut])
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[TransactionOut]:
    rows, total = await wallet_svc.list_transactions(db, user, page=page, page_size=page_size)
    items = [
        TransactionOut(
            id=t.id,
            type=t.type,
            currency=t.currency,
            amount=float(t.amount),
            ref_sku=t.ref_sku,
            meta=t.meta or {},
            created_at=t.created_at,
        )
        for t in rows
    ]
    return Page[TransactionOut](items=items, total=total, page=page, page_size=page_size)


@router.post("/recharge", response_model=RechargeOut)
async def recharge(
    payload: RechargeIn,
    user: User = Depends(get_current_user),
) -> RechargeOut:
    """Return deposit address. Stubbed for now — replace with real PSP."""
    addr_map = {
        "TRC20": "TXXXuserDepositAddrTRC20PlaceholderXXXX",
        "ERC20": "0xUserDepositAddrERC20PlaceholderxxxxxXX",
        "BEP20": "0xUserDepositAddrBEP20PlaceholderxxxxxXX",
    }
    return RechargeOut(
        address=addr_map.get(payload.chain, addr_map["TRC20"]),
        currency=payload.currency,
        chain=payload.chain,
        memo=f"uid:{user.id}",
        qr_code_url=None,
    )


@router.post("/withdraw", response_model=MessageOut)
async def withdraw(
    payload: WithdrawIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    await wallet_svc.withdraw(
        db, user,
        amount=Decimal(str(payload.amount)),
        currency=payload.currency,
        chain=payload.chain,
        address=payload.address,
    )
    return MessageOut(message="withdraw_pending")
