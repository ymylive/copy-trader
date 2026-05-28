"""Dashboard aggregation endpoints."""
from __future__ import annotations

import time
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

router = APIRouter()


# Very small in-process TTL cache for the public endpoints.
_news_cache: dict[str, tuple[float, List[NewsItem]]] = {}
_market_cache: dict[str, tuple[float, MarketOverviewOut]] = {}
_NEWS_TTL_S = 60
_MARKET_TTL_S = 30


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
    """Cached crypto news feed (60s TTL). Stubbed for M0."""
    key = "default"
    ts, cached = _news_cache.get(key, (0.0, []))
    if cached and time.time() - ts < _NEWS_TTL_S:
        return cached
    now = datetime.utcnow()
    items = [
        NewsItem(
            id="n1",
            title="BTC 突破 70k 心理关口，市场资金费率走高",
            url=None,
            source="CoinTelegraph",
            published_at=now - timedelta(minutes=15),
            tags=["BTC", "spot"],
        ),
        NewsItem(
            id="n2",
            title="Hyperliquid 新增多个高 PnL Vault，链上跟单热度回暖",
            url=None,
            source="The Block",
            published_at=now - timedelta(hours=1),
            tags=["Hyperliquid", "Vault"],
        ),
        NewsItem(
            id="n3",
            title="OKX 公开带单页面 API 重构，前 20 名带单员胜率刷新",
            url=None,
            source="OKX Blog",
            published_at=now - timedelta(hours=3),
            tags=["OKX", "Copy"],
        ),
    ]
    _news_cache[key] = (time.time(), items)
    return items


@router.get("/market", response_model=MarketOverviewOut)
async def market(_user: User = Depends(get_current_user)) -> MarketOverviewOut:
    key = "default"
    ts, cached = _market_cache.get(key, (0.0, None))  # type: ignore[arg-type]
    if cached is not None and time.time() - ts < _MARKET_TTL_S:
        return cached
    snap = MarketOverviewOut(
        btc_price_usdt=68250.31,
        btc_change_24h=1.42,
        fear_greed_index=62,
        liquidations_24h_usdt=128_400_000.0,
        open_interest_usdt=24_650_000_000.0,
        funding_rate_btc=0.00012,
        long_short_ratio=1.08,
        updated_at=datetime.utcnow(),
    )
    _market_cache[key] = (time.time(), snap)
    return snap
