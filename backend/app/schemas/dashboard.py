"""Dashboard aggregation schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.schemas.common import APIModel


class DashboardSummaryOut(APIModel):
    total_assets_usdt: float
    account_count: int
    active_account_count: int
    cumulative_pnl: float
    today_pnl: float
    running_configs: int


class NewsItem(APIModel):
    id: str
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    published_at: datetime
    tags: List[str] = []


class MarketOverviewOut(APIModel):
    btc_price_usdt: float
    btc_change_24h: float
    fear_greed_index: int
    liquidations_24h_usdt: float
    open_interest_usdt: float
    funding_rate_btc: float
    long_short_ratio: float
    updated_at: datetime
