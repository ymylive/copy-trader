"""Trader catalogue + per-user watchlist."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound
from app.core.security import encrypt_secret
from app.deps import get_current_user, get_db
from app.db.models import Trader, TraderWatchlist, User
from app.schemas.common import MessageOut, Page
from app.schemas.traders import TraderOut, WatchlistIn, WatchlistOut

router = APIRouter()


@router.get("/", response_model=Page[TraderOut])
async def list_traders(
    source: Optional[str] = Query(default=None),
    exchange: Optional[str] = Query(default=None),
    listed: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[TraderOut]:
    stmt = select(Trader)
    count_stmt = select(func.count()).select_from(Trader)
    if source:
        stmt = stmt.where(Trader.source == source)
        count_stmt = count_stmt.where(Trader.source == source)
    if exchange:
        stmt = stmt.where(Trader.exchange == exchange)
        count_stmt = count_stmt.where(Trader.exchange == exchange)
    if listed is not None:
        stmt = stmt.where(Trader.listed == listed)
        count_stmt = count_stmt.where(Trader.listed == listed)
    if search:
        like = f"%{search}%"
        cond = or_(Trader.display_name.ilike(like), Trader.external_id.ilike(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    total = (await db.execute(count_stmt)).scalar_one()
    # SQLite supports NULLS LAST since 3.30; we keep it simple.
    rows = await db.execute(
        stmt.order_by(desc(Trader.last_active_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [TraderOut.model_validate(t) for t in rows.scalars()]
    return Page[TraderOut](items=items, total=int(total), page=page, page_size=page_size)


@router.get("/{trader_id}", response_model=TraderOut)
async def get_trader(
    trader_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TraderOut:
    tr = await db.get(Trader, trader_id)
    if tr is None:
        raise NotFound("trader not found", code="trader_not_found")
    return TraderOut.model_validate(tr)


@router.post("/watchlist", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
async def add_watchlist(
    payload: WatchlistIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchlistOut:
    # Find-or-create the trader row.
    tr = await db.scalar(
        select(Trader).where(
            Trader.source == payload.source, Trader.external_id == payload.external_id
        )
    )
    if tr is None:
        tr = Trader(
            source=payload.source,
            external_id=payload.external_id,
            display_name=payload.display_name,
            exchange=payload.exchange,
            listed=False,  # user-added → not in public catalogue
        )
        db.add(tr)
        await db.flush()

    watch = TraderWatchlist(
        user_id=user.id,
        trader_id=tr.id,
        cookie_enc=encrypt_secret(payload.cookie) if payload.cookie else None,
    )
    db.add(watch)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise Conflict("already in watchlist", code="already_watching") from exc

    return WatchlistOut(
        id=watch.id,
        trader_id=tr.id,
        created_at=watch.created_at,
        trader=TraderOut.model_validate(tr),
    )


@router.delete("/watchlist/{watch_id}", response_model=MessageOut)
async def remove_watchlist(
    watch_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    watch = await db.get(TraderWatchlist, watch_id)
    if watch is None or watch.user_id != user.id:
        raise NotFound("watch item not found", code="watch_not_found")
    await db.delete(watch)
    return MessageOut(message="removed")
