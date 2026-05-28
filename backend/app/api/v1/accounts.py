"""Exchange account endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.accounts import (
    APIKeyIn,
    BalanceOut,
    ExchangeAccountCreate,
    ExchangeAccountOut,
    ExchangeAccountUpdate,
    NavPointOut,
    PositionOut,
)
from app.schemas.common import MessageOut
from app.services import accounts as acc_svc

router = APIRouter()


def _to_out(acc) -> ExchangeAccountOut:
    return ExchangeAccountOut(
        id=acc.id,
        user_id=acc.user_id,
        alias=acc.alias,
        tier=acc.tier,
        exchange=acc.exchange,
        uid=acc.uid,
        leverage_default=acc.leverage_default,
        status=acc.status,
        egress_ips=list(acc.egress_ips or []),
        activated_at=acc.activated_at,
        service_expires_at=acc.service_expires_at,
        has_api_key=bool(acc.api_key_enc),
        created_at=acc.created_at,
    )


@router.get("/", response_model=List[ExchangeAccountOut])
async def list_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ExchangeAccountOut]:
    accs = await acc_svc.list_accounts(db, user)
    return [_to_out(a) for a in accs]


@router.post("/", response_model=ExchangeAccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: ExchangeAccountCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeAccountOut:
    acc = await acc_svc.create_account(
        db, user,
        alias=payload.alias,
        tier=payload.tier,
        exchange=payload.exchange,
        leverage_default=payload.leverage_default,
    )
    return _to_out(acc)


@router.patch("/{account_id}", response_model=ExchangeAccountOut)
async def update_account(
    account_id: int,
    payload: ExchangeAccountUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeAccountOut:
    acc = await acc_svc.update_account(
        db, user, account_id,
        alias=payload.alias,
        leverage_default=payload.leverage_default,
    )
    return _to_out(acc)


@router.post("/{account_id}/apikey", response_model=ExchangeAccountOut)
async def set_api_key(
    account_id: int,
    payload: APIKeyIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeAccountOut:
    acc = await acc_svc.set_api_key(
        db, user, account_id,
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        passphrase=payload.passphrase,
        uid=payload.uid,
    )
    return _to_out(acc)


@router.post("/{account_id}/activate", response_model=ExchangeAccountOut)
async def activate_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeAccountOut:
    acc = await acc_svc.activate_account(db, user, account_id)
    return _to_out(acc)


@router.delete("/{account_id}", response_model=MessageOut)
async def delete_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    await acc_svc.delete_account(db, user, account_id)
    return MessageOut(message="deleted")


@router.get("/{account_id}/balance", response_model=BalanceOut)
async def get_balance(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BalanceOut:
    """Cached balance (would be written by execution_engine to Redis).

    For now we attempt to read from Redis; if missing return a stub.
    """
    acc = await acc_svc.get_account(db, user, account_id)
    cached = await _read_balance_cache(acc.id)
    if cached is None:
        return BalanceOut(
            account_id=acc.id,
            total_balance=0.0,
            available_balance=0.0,
            unrealized_pnl=0.0,
            updated_at=datetime.utcnow(),
        )
    return BalanceOut(**cached)


async def _read_balance_cache(account_id: int) -> Optional[dict]:
    try:
        import redis.asyncio as redis  # local import; optional dep
        s = get_settings()
        client = redis.from_url(s.redis_url, decode_responses=True)
        raw = await client.get(f"balance:{account_id}")
        await client.aclose()
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


@router.get("/{account_id}/positions", response_model=List[PositionOut])
async def get_positions(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PositionOut]:
    await acc_svc.get_account(db, user, account_id)  # auth check
    rows = await acc_svc.latest_positions(db, account_id)
    return [
        PositionOut(
            symbol=r.symbol,
            side=r.side,
            qty=float(r.qty),
            entry_px=float(r.entry_px) if r.entry_px is not None else None,
            lev=float(r.lev) if r.lev is not None else None,
            margin=float(r.margin) if r.margin is not None else None,
            unrealized_pnl=float(r.unrealized_pnl) if r.unrealized_pnl is not None else None,
            ts=r.ts,
        )
        for r in rows
    ]


@router.get("/{account_id}/nav", response_model=List[NavPointOut])
async def get_nav_curve(
    account_id: int,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=20000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[NavPointOut]:
    await acc_svc.get_account(db, user, account_id)
    rows = await acc_svc.nav_curve(db, account_id, start=start, end=end, limit=limit)
    return [
        NavPointOut(
            ts=r.ts,
            total_balance=float(r.total_balance),
            realized_pnl=float(r.realized_pnl),
            unrealized_pnl=float(r.unrealized_pnl),
        )
        for r in rows
    ]
