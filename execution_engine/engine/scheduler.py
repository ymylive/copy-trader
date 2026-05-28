"""APScheduler — periodic jobs.

Jobs:
  * snapshot positions   → positions_snapshots  (every minute)
  * write NAV curve      → nav_curve            (every hour)
  * refill scan          → runner.evaluate_risk (every 10s, but the
                            engine already runs that internally; this
                            is here for symmetry)
  * subscription expiry  → check exchange_accounts.service_expires_at
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update

from .config import get_settings
from .db import session_scope
from .follower import FollowerEngine
from .logging_setup import get_logger
from .models import ExchangeAccount, NavCurve, PositionSnapshot, SubscriptionResource

log = get_logger(__name__)


class EngineScheduler:
    def __init__(self, engine: FollowerEngine) -> None:
        self.engine = engine
        self.settings = get_settings()
        self.sched = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        if not self.settings.enable_scheduler:
            log.info("scheduler_disabled")
            return
        self.sched.add_job(
            self._snapshot_positions,
            "interval",
            seconds=self.settings.snapshot_interval_sec,
            id="snap_positions",
            max_instances=1,
        )
        self.sched.add_job(
            self._snapshot_nav,
            "interval",
            seconds=self.settings.nav_interval_sec,
            id="snap_nav",
            max_instances=1,
        )
        self.sched.add_job(
            self._renew_subscriptions,
            "interval",
            seconds=3600,
            id="renew_subs",
            max_instances=1,
        )
        self.sched.start()
        log.info("scheduler_started")

    async def shutdown(self) -> None:
        if self.sched.running:
            self.sched.shutdown(wait=False)

    # ── jobs ──────────────────────────────────────────────────
    async def _snapshot_positions(self) -> None:
        now = datetime.now(tz=timezone.utc)
        snaps: list[PositionSnapshot] = []
        for runner in list(self.engine.runners.values()):
            try:
                positions = await runner.adapter.get_positions()
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "snap_pos_failed",
                    error=str(exc),
                    config_id=runner.ctx.config_id,
                )
                continue
            for p in positions:
                snaps.append(
                    PositionSnapshot(
                        ts=now,
                        exchange_account_id=runner.ctx.exchange_account_id,
                        symbol=p.symbol,
                        side=p.side,
                        qty=p.qty,
                        entry_px=p.entry_px,
                        lev=p.lev,
                        margin=p.margin,
                        unrealized_pnl=p.unrealized_pnl,
                    )
                )
        if not snaps:
            return
        async with session_scope() as ses:
            ses.add_all(snaps)
            await ses.commit()

    async def _snapshot_nav(self) -> None:
        now = datetime.now(tz=timezone.utc)
        rows: list[NavCurve] = []
        for runner in list(self.engine.runners.values()):
            try:
                nav = await runner.adapter.get_total_assets()
                bal = await runner.adapter.get_balance()
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "snap_nav_failed", error=str(exc), config_id=runner.ctx.config_id
                )
                continue
            rows.append(
                NavCurve(
                    ts=now,
                    exchange_account_id=runner.ctx.exchange_account_id,
                    total_balance=bal,
                    realized_pnl=Decimal("0"),
                    unrealized_pnl=(nav - bal),
                )
            )
        if not rows:
            return
        async with session_scope() as ses:
            ses.add_all(rows)
            await ses.commit()

    async def _renew_subscriptions(self) -> None:
        """Auto-renew subscription_resources whose ``auto_renew`` flag is set.

        Actual payment is a wallet operation we delegate to the backend
        — here we simply mark candidates so an internal endpoint picks
        them up. For now, just log.
        """
        now = datetime.now(tz=timezone.utc)
        async with session_scope() as ses:
            q = await ses.execute(
                select(SubscriptionResource).where(
                    SubscriptionResource.auto_renew.is_(True),
                    SubscriptionResource.expires_at <= now,
                )
            )
            expired = q.scalars().all()
            if expired:
                log.info("subs_expired_auto_renew_candidates", count=len(expired))
