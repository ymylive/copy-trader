"""bicoin.com.cn proxy-login scraper — **P2 stub**.

bicoin's data source is *user-uploaded API keys*; there is no public API.  The
end-user uploads their own bicoin account credentials (password or session
cookie) via the backend, which writes them to an encrypted vault and triggers
this worker to pull persona-bound data.

This file is a runnable skeleton so the rest of the system has a stable
entry-point name (``--worker bicoin_scraper``) — the actual scraper requires
either Selenium/Playwright with anti-fingerprinting or a successful frida-hook
of the native sign(...) algorithm, neither of which fits in the initial cut.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time

import structlog

from signal_workers.common.event_bus import EventBus
from signal_workers.common.redis_helper import get_redis
from signal_workers.common.trader_registry import TraderRegistry

log = structlog.get_logger(__name__)

POLL_INTERVAL = float(os.environ.get("BICOIN_POLL_SEC", "30"))


async def run(args: argparse.Namespace) -> None:
    stop_event: asyncio.Event = getattr(args, "stop_event", asyncio.Event())

    redis_client = await get_redis(args.redis_url, dry_run=args.dry_run)
    bus = EventBus(redis_client)
    registry = TraderRegistry(dsn=args.database_url, source_filter="bicoin")

    log.warning(
        "bicoin_scraper.stub_mode",
        note="Stub — needs user-uploaded credentials + Playwright. See TODO.",
    )

    while not stop_event.is_set():
        try:
            await registry.refresh()
            traders = registry.snapshot()
            log.info("bicoin_scraper.heartbeat", n_traders=len(traders), ts=int(time.time()))
        except Exception as exc:  # noqa: BLE001
            log.warning("bicoin_scraper.heartbeat_err", err=str(exc))
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL)
        except asyncio.TimeoutError:
            pass

    log.info("bicoin_scraper.shutting_down")
    await bus.aclose()
    await registry.aclose()


# ---------------------------------------------------------------------------
# TODO list
# ---------------------------------------------------------------------------
#
# 1. Credential intake
#    - execution_engine writes the user's bicoin (username, password) into a
#      vault keyed by user_id, then enqueues a job onto Redis Stream
#      `stream:bicoin:login-requests`.
#    - This worker XREADGROUP-consumes that stream, performs login, stores
#      the resulting session cookie back to the vault.
#
# 2. Login flow (Playwright)
#    - `bicoin.com.cn/login` -> fill form -> handle slider captcha (third-party
#      OCR or 2Captcha).  Save Set-Cookie -> vault.
#    - Refresh cookie every 24 h or on 401.
#
# 3. Data pull endpoints (paths to be re-verified at deploy time):
#    - GET /api/follow/list  -> 我关注的大佬
#    - GET /api/users/detail/<uid>  -> 大佬持仓
#    - GET /api/positions/list?uid=<uid>
#
#    bicoin native client uses `sign + data` envelope:
#        body = { data: <base64-encrypted-json>, sign: <hmac-sha256> }
#    The web version may have a simpler scheme — check first.
#
# 4. Parser
#    - bicoin持仓字段类似 OKX：{symbol, side, qty, entry_px, lev, margin, upl}
#    - Convert via signal_workers.common.normalizer.normalize_symbol(..., source="bicoin").
#    - Emit position_snapshot every 30–60 s; diff to derive open/close events
#      (same diff algorithm as okx_public).
#
# 5. Risk handling
#    - bicoin actively bans multi-device logins; pin one session per user.
#    - Add prometheus counter bicoin_login_failures_total.
#
# 6. Legal note
#    - Make sure execution_engine displays an explicit consent dialog before
#      uploading bicoin password to the vault.  See README §七.6 (compliance).
