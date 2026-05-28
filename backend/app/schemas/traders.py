"""Trader schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.schemas.common import APIModel


class TraderOut(APIModel):
    id: int
    source: str
    external_id: str
    display_name: Optional[str] = None
    exchange: Optional[str] = None
    meta: Dict[str, Any] = {}
    stats: Dict[str, Any] = {}
    last_active_at: Optional[datetime] = None
    listed: bool = True


class WatchlistIn(APIModel):
    source: str
    external_id: str
    display_name: Optional[str] = None
    exchange: Optional[str] = None
    cookie: Optional[str] = None  # for private/hidden sources


class WatchlistOut(APIModel):
    id: int
    trader_id: int
    created_at: datetime
    trader: TraderOut
