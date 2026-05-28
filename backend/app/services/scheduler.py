"""APScheduler jobs (auto-renew, cookie refresh, NAV roll-up...)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db.base import session_scope
from app.db.models import SubscriptionResource, User

log = logging.getLogger(__name__)


def register_jobs(scheduler) -> None:  # noqa: ANN001
    scheduler.add_job(scan_subscriptions_for_renew, "interval", hours=6, id="auto_renew_scan")
    log.info("scheduler.jobs_registered=%s", [j.id for j in scheduler.get_jobs()])


async def scan_subscriptions_for_renew() -> None:
    """Find subscription_resources within 24h of expiry with auto_renew=True
    and renew them by debiting the user wallet."""
    cutoff = datetime.utcnow() + timedelta(hours=24)
    async with session_scope() as db:
        rows = await db.execute(
            select(SubscriptionResource).where(
                SubscriptionResource.auto_renew.is_(True),
                SubscriptionResource.expires_at <= cutoff,
                SubscriptionResource.expires_at >= datetime.utcnow(),
            )
        )
        items = list(rows.scalars().all())
        if not items:
            return
        log.info("scheduler.auto_renew candidates=%d", len(items))
        for res in items:
            user = await db.get(User, res.user_id)
            if user is None:
                continue
            # Delegate to shop service for renewal logic
            try:
                from app.services import shop as shop_svc
                await shop_svc.purchase(
                    db, user,
                    sku=res.sku,
                    months=1,
                    bound_account_id=res.bound_account_id,
                    auto_renew=True,
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("auto_renew_failed resource=%s err=%s", res.id, exc)
        await db.commit()
