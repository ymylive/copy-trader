"""Dashboard aggregation endpoints."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.db.models import (
    CopyConfig,
    ExchangeAccount,
    NavPoint,
    User,
    WalletBalance,
)
from app.schemas.dashboard import (
    DashboardSummaryOut,
    MarketOverviewOut,
    NewsItem,
)
from app.services.market_feed import fetch_market_overview, fetch_news

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryOut)
async def summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryOut:
    account_count = (
        await db.execute(
            select(func.count())
            .select_from(ExchangeAccount)
            .where(ExchangeAccount.user_id == user.id)
        )
    ).scalar_one()
    active_account_count = (
        await db.execute(
            select(func.count())
            .select_from(ExchangeAccount)
            .where(ExchangeAccount.user_id == user.id, ExchangeAccount.status == "active")
        )
    ).scalar_one()

    # Wallet
    wallet_total = (
        await db.execute(
            select(func.coalesce(func.sum(WalletBalance.amount), 0))
            .where(WalletBalance.user_id == user.id, WalletBalance.currency == "USDT")
        )
    ).scalar_one()

    # Aggregate latest NAV per account: take most recent point per account
    sub = (
        select(
            NavPoint.exchange_account_id.label("aid"),
            func.max(NavPoint.ts).label("max_ts"),
        )
        .join(ExchangeAccount, ExchangeAccount.id == NavPoint.exchange_account_id)
        .where(ExchangeAccount.user_id == user.id)
        .group_by(NavPoint.exchange_account_id)
        .subquery()
    )
    nav_q = await db.execute(
        select(NavPoint).join(
            sub,
            (NavPoint.exchange_account_id == sub.c.aid) & (NavPoint.ts == sub.c.max_ts),
        )
    )
    nav_rows = list(nav_q.scalars().all())
    total_balance_now = sum((float(n.total_balance) for n in nav_rows), 0.0)
    cumulative_pnl = sum((float(n.realized_pnl) + float(n.unrealized_pnl) for n in nav_rows), 0.0)

    # Today PnL: difference between latest and earliest-of-today NAV
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_q = await db.execute(
        select(
            NavPoint.exchange_account_id,
            func.min(NavPoint.total_balance),
            func.max(NavPoint.total_balance),
        )
        .join(ExchangeAccount, ExchangeAccount.id == NavPoint.exchange_account_id)
        .where(ExchangeAccount.user_id == user.id, NavPoint.ts >= today_start)
        .group_by(NavPoint.exchange_account_id)
    )
    today_pnl = 0.0
    for _aid, lo, hi in today_q.all():
        try:
            today_pnl += float(hi) - float(lo)
        except (TypeError, ValueError):
            continue

    running_configs = (
        await db.execute(
            select(func.count())
            .select_from(CopyConfig)
            .where(CopyConfig.user_id == user.id, CopyConfig.status == "running")
        )
    ).scalar_one()

    return DashboardSummaryOut(
        total_assets_usdt=float(wallet_total) + total_balance_now,
        account_count=int(account_count),
        active_account_count=int(active_account_count),
        cumulative_pnl=cumulative_pnl,
        today_pnl=today_pnl,
        running_configs=int(running_configs),
    )


@router.get("/news", response_model=List[NewsItem])
async def news(_user: User = Depends(get_current_user)) -> List[NewsItem]:
    """Live crypto news feed (CryptoPanic, 60s TTL + last-good fallback)."""
    raw = await fetch_news(limit=10)
    items: List[NewsItem] = []
    now = datetime.utcnow()
    for i, r in enumerate(raw):
        try:
            pub = r.get("published_at")
            if isinstance(pub, str):
                # CryptoPanic returns ISO-8601; tolerate Z suffix
                pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            elif not isinstance(pub, datetime):
                pub = now - timedelta(minutes=15 * (i + 1))
        except Exception:  # noqa: BLE001
            pub = now - timedelta(minutes=15 * (i + 1))
        items.append(NewsItem(
            id=r.get("id") or f"n{i}",
            title=r.get("title") or "",
            url=r.get("url"),
            source=r.get("source"),
            published_at=pub,
            tags=r.get("tags") or [],
        ))
    return items


@router.get("/market", response_model=MarketOverviewOut)
async def market(_user: User = Depends(get_current_user)) -> MarketOverviewOut:
    """Live market overview (CoinGecko + alternative.me + Binance Futures)."""
    snap = await fetch_market_overview()
    return MarketOverviewOut(**snap)
