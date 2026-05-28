"""Binance Lead-Trader / Leaderboard scraper — **P1 stub**.

This worker is intentionally a *runnable skeleton*: it boots cleanly, loops
forever, exposes metrics, and exits gracefully on signal — but does NOT yet
implement the cookie-pool / WAF-bypass logic required to actually scrape
``bapi/futures/v2/private/...``.

Why a stub?  Per the research report (``signal_sources_research.md`` §1):

* The current endpoints (``/bapi/futures/v2/private/future/leaderboard/...``)
  require web-login Cookie + ``aws-waf-token`` + ``cf_clearance`` + JA3-faked
  TLS fingerprint. None of those can be implemented in 1 hour of code.
* Doing it right requires (a) a residential-IP pool, (b) ``curl_cffi`` /
  ``tls-client`` for JA3 spoofing, (c) headless-browser cookie harvesting
  every 7–30 days.

The full TODO list lives at the bottom of this module so a follow-up agent
can pick up exactly where we stopped.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time

import structlog

from signal_workers.common.event_bus import EventBus
from signal_workers.common.ratelimit import TokenBucket
from signal_workers.common.redis_helper import get_redis
from signal_workers.common.trader_registry import TraderRegistry

log = structlog.get_logger(__name__)

POLL_INTERVAL = float(os.environ.get("BINANCE_POLL_SEC", "10"))
GLOBAL_RATE = float(os.environ.get("BINANCE_RPS", "0.5"))


def _load_cookies_from_env() -> list[str]:
    """Cookies are provisioned via ``BINANCE_COOKIES=<c1>;<c2>;...`` env var.

    Empty cookie pool is fine — the worker will idle and surface the fact
    via metrics / logs.
    """
    raw = os.environ.get("BINANCE_COOKIES", "")
    return [c.strip() for c in raw.split(";") if c.strip()]


async def run(args: argparse.Namespace) -> None:
    """Stub run-loop — sits idle, logs a heartbeat, emits nothing."""
    stop_event: asyncio.Event = getattr(args, "stop_event", asyncio.Event())

    redis_client = await get_redis(args.redis_url, dry_run=args.dry_run)
    bus = EventBus(redis_client)
    registry = TraderRegistry(dsn=args.database_url, source_filter="binance_lead")
    _bucket = TokenBucket(rate=GLOBAL_RATE)  # placeholder for future implementation

    cookies = _load_cookies_from_env()
    log.warning(
        "binance_lead.stub_mode",
        cookies_loaded=len(cookies),
        note="Stub — no actual scraping yet. See TODO at bottom of main.py.",
    )

    while not stop_event.is_set():
        try:
            await registry.refresh()
            traders = registry.snapshot()
            log.info(
                "binance_lead.heartbeat",
                ts=int(time.time()),
                n_traders=len(traders),
                cookies=len(cookies),
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("binance_lead.heartbeat_err", err=str(exc))

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL)
        except asyncio.TimeoutError:
            pass

    log.info("binance_lead.shutting_down")
    await bus.aclose()
    await registry.aclose()


# ---------------------------------------------------------------------------
# TODO list for the implementation pass
# ---------------------------------------------------------------------------
#
# 1. HTTP client
#    - Use `curl_cffi` (impersonate="chrome120") to spoof TLS JA3.
#    - Pool of residential IPs configured via `BINANCE_PROXIES=<url1>,<url2>,...`
#      (env). Round-robin per request; ban an IP for 30 min on 403/429.
#
# 2. Cookie pool
#    - Each cookie in `BINANCE_COOKIES` is one full web-login Cookie header.
#    - Required fields: p20t, p21t, cr00, bnc-uuid, aws-waf-token, cf_clearance.
#    - Build `BinanceCookieJar` that hot-swaps cookies on 403/`-1100` responses.
#    - Refresh aws-waf-token every ~10 min by re-hitting a public Binance page
#      with a Playwright session (background worker).
#
# 3. Endpoints to call (POST JSON, all on www.binance.com):
#    - /bapi/futures/v2/private/future/leaderboard/searchLeaderboard
#    - /bapi/futures/v2/private/future/leaderboard/getOtherPosition
#      payload: {"encryptedUid": <uid>, "tradeType": "PERPETUAL"}
#    - /bapi/futures/v2/private/future/leaderboard/getOtherPerformance
#    - /bapi/futures/v2/private/future/leaderboard/getLeaderboardRank
#
# 4. Parser
#    - `otherPositionRetList[]` -> diff against previous snapshot just like
#      okx_public.diff. The fields here are
#      {symbol, entryPrice, markPrice, pnl, roe, amount, updateTime,
#       leverage, tradeBefore, yellow, positionShared}.
#    - When positionShared is False, the row is omitted entirely (hidden
#      position). Surface a `traders.meta.hidden_positions_detected = true`.
#    - Use signal_workers.common.normalizer to convert BTCUSDT → BTC-USDT-SWAP.
#
# 5. Risk handling
#    - Detect WAF challenge response (HTML body containing
#      "aws-waf-token" mismatch) → mark cookie+IP burned, sleep 5 min.
#    - Emit prometheus counter binance_waf_blocks_total{ip,cookie}.
#
# 6. Cadence
#    - Web front-end polls 5s; we mirror at 5–10s per trader.  For >100
#      traders, fan out across multiple cookies/IPs.
#
# 7. Schema mapping per docs/event_schema.md:
#    - source="binance_lead"
#    - trader_id = encryptedUid (NOT username — username can collide)
#    - kind="order_open"|"order_close"|"position_snapshot"
#
# Refs:
#   research/signal_sources_research.md §1
#   https://github.com/Nunnito/Binance-Futures-Leaderboard-API
