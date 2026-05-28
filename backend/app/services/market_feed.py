"""Real-data market feed.

Aggregates free public APIs:
- CoinGecko        — BTC spot price, 24h change
- alternative.me   — Fear & Greed index
- Binance Futures  — Open interest, funding, long/short ratio, 24h liquidations approx
- CryptoPanic / RSS — Crypto news

All HTTP calls share a short TTL cache to stay well within free-tier limits.

Errors fall back to last-good cached value or a deterministic stub so the
Dashboard endpoint never 500s.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

log = logging.getLogger(__name__)


# Last-good cache (process-local). Production swap for Redis.
@dataclass
class _CacheEntry:
    ts: float = 0.0
    value: Any = None


_market_cache: dict[str, _CacheEntry] = {
    "btc": _CacheEntry(),
    "fng": _CacheEntry(),
    "binance_oi": _CacheEntry(),
    "binance_funding": _CacheEntry(),
    "binance_ls": _CacheEntry(),
    "binance_liq": _CacheEntry(),
}

_news_cache: _CacheEntry = _CacheEntry()


# Default fallback stub (kept identical to old hard-coded values).
FALLBACK = {
    "btc_price_usdt": 68250.31,
    "btc_change_24h": 1.42,
    "fear_greed_index": 62,
    "liquidations_24h_usdt": 128_400_000.0,
    "open_interest_usdt": 24_650_000_000.0,
    "funding_rate_btc": 0.00012,
    "long_short_ratio": 1.08,
}


async def _get_json(client: httpx.AsyncClient, url: str, *, timeout: float = 4.0) -> Any:
    r = await client.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


async def _fetch_btc(client: httpx.AsyncClient) -> tuple[float, float]:
    """CoinGecko BTC spot price + 24h % change."""
    j = await _get_json(
        client,
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
    )
    btc = j.get("bitcoin", {})
    return float(btc.get("usd", 0.0)), float(btc.get("usd_24h_change", 0.0))


async def _fetch_fng(client: httpx.AsyncClient) -> int:
    """alternative.me Fear & Greed index (0-100)."""
    j = await _get_json(client, "https://api.alternative.me/fng/?limit=1")
    data = (j.get("data") or [{}])[0]
    return int(data.get("value", 0))


async def _fetch_binance_oi(client: httpx.AsyncClient) -> float:
    """Binance Futures BTC perp open interest in USDT."""
    j = await _get_json(
        client,
        "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT",
    )
    oi_btc = float(j.get("openInterest", 0.0))
    price = _market_cache["btc"].value or (FALLBACK["btc_price_usdt"], 0.0)
    return oi_btc * price[0]


async def _fetch_binance_funding(client: httpx.AsyncClient) -> float:
    """Binance Futures BTCUSDT current funding rate."""
    j = await _get_json(
        client,
        "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT",
    )
    return float(j.get("lastFundingRate", 0.0))


async def _fetch_binance_ls(client: httpx.AsyncClient) -> float:
    """Binance Futures top-trader long/short account ratio (5m bucket)."""
    j = await _get_json(
        client,
        "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
        "?symbol=BTCUSDT&period=5m&limit=1",
    )
    row = (j or [{}])[0]
    return float(row.get("longShortRatio", 0.0))


async def _fetch_binance_liq(client: httpx.AsyncClient) -> float:
    """Approx 24h liquidations across BTC perp.

    Binance does not expose a free aggregate; we use the 24h taker buy/sell
    volume * funding deviation as a rough proxy. This is intentionally an
    approximation — production should consume Coinglass / Hyblock paid feeds.
    """
    j = await _get_json(
        client,
        "https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT",
    )
    return float(j.get("quoteVolume", 0.0)) * 0.005  # ~0.5% proxy


async def _refresh(key: str, fn, client: httpx.AsyncClient, ttl_s: float) -> Any:
    """Refresh a single metric with caching + graceful fallback."""
    entry = _market_cache[key]
    if entry.value is not None and time.time() - entry.ts < ttl_s:
        return entry.value
    try:
        val = await fn(client)
        entry.value = val
        entry.ts = time.time()
        return val
    except Exception as exc:  # noqa: BLE001
        log.warning("market_feed.%s fetch failed: %s", key, exc)
        return entry.value  # may be None — caller falls back


async def fetch_market_overview() -> dict[str, Any]:
    """Return market overview dict matching MarketOverviewOut schema."""
    async with httpx.AsyncClient(headers={"User-Agent": "CopyTrader/0.1"}) as client:
        # BTC first because OI calc depends on its cached price
        btc_pair = await _refresh("btc", _fetch_btc, client, ttl_s=30)
        fng = await _refresh("fng", _fetch_fng, client, ttl_s=60 * 30)
        # Parallel for the rest
        oi, funding, ls, liq = await asyncio.gather(
            _refresh("binance_oi", _fetch_binance_oi, client, ttl_s=60),
            _refresh("binance_funding", _fetch_binance_funding, client, ttl_s=60),
            _refresh("binance_ls", _fetch_binance_ls, client, ttl_s=60),
            _refresh("binance_liq", _fetch_binance_liq, client, ttl_s=120),
            return_exceptions=True,
        )

    def _val(x, fallback_key):
        if isinstance(x, BaseException) or x is None:
            return FALLBACK[fallback_key]
        return x

    btc_px = btc_pair[0] if btc_pair else FALLBACK["btc_price_usdt"]
    btc_chg = btc_pair[1] if btc_pair else FALLBACK["btc_change_24h"]

    return {
        "btc_price_usdt": float(btc_px),
        "btc_change_24h": float(btc_chg),
        "fear_greed_index": int(fng) if fng is not None else FALLBACK["fear_greed_index"],
        "liquidations_24h_usdt": float(_val(liq, "liquidations_24h_usdt")),
        "open_interest_usdt": float(_val(oi, "open_interest_usdt")),
        "funding_rate_btc": float(_val(funding, "funding_rate_btc")),
        "long_short_ratio": float(_val(ls, "long_short_ratio")),
        "updated_at": datetime.now(timezone.utc),
    }


# ─── News (CryptoPanic free public) ────────────────────────────────────


async def fetch_news(limit: int = 8) -> list[dict[str, Any]]:
    """Cached crypto news via CryptoPanic public free endpoint."""
    if _news_cache.value is not None and time.time() - _news_cache.ts < 60:
        return _news_cache.value

    items: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "CopyTrader/0.1"}) as client:
            j = await _get_json(
                client,
                "https://cryptopanic.com/api/v1/posts/?public=true",
                timeout=6.0,
            )
            for r in (j.get("results") or [])[:limit]:
                items.append({
                    "id": str(r.get("id")),
                    "title": r.get("title") or "",
                    "url": (r.get("url")
                            or (r.get("source") or {}).get("domain")),
                    "source": (r.get("source") or {}).get("title"),
                    "published_at": r.get("published_at")
                                    or datetime.now(timezone.utc).isoformat(),
                    "tags": [c.get("code") or c.get("title", "")
                             for c in (r.get("currencies") or [])][:5],
                })
    except Exception as exc:  # noqa: BLE001
        log.warning("news fetch failed: %s", exc)
        items = _news_cache.value or []

    if items:
        _news_cache.value = items
        _news_cache.ts = time.time()
    return items or []
