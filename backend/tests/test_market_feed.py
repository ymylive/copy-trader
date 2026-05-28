"""Tests for the real-data market feed adapter."""
from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.services import market_feed


@pytest.mark.asyncio
@respx.mock
async def test_market_overview_aggregates_external_apis(monkeypatch):
    """Each external endpoint returns canned JSON → aggregated dict is correct."""
    # Reset module cache so we hit the mocks fresh
    for k in market_feed._market_cache:
        market_feed._market_cache[k].value = None
        market_feed._market_cache[k].ts = 0.0

    respx.get("https://api.coingecko.com/api/v3/simple/price").mock(
        return_value=Response(200, json={"bitcoin": {"usd": 74180.0, "usd_24h_change": -1.97}})
    )
    respx.get("https://api.alternative.me/fng/").mock(
        return_value=Response(200, json={"data": [{"value": "22"}]})
    )
    respx.get("https://fapi.binance.com/fapi/v1/openInterest").mock(
        return_value=Response(200, json={"openInterest": "101234.5"})
    )
    respx.get("https://fapi.binance.com/fapi/v1/premiumIndex").mock(
        return_value=Response(200, json={"lastFundingRate": "0.00010"})
    )
    respx.get("https://fapi.binance.com/futures/data/topLongShortAccountRatio").mock(
        return_value=Response(200, json=[{"longShortRatio": "1.69"}])
    )
    respx.get("https://fapi.binance.com/fapi/v1/ticker/24hr").mock(
        return_value=Response(200, json={"quoteVolume": "75050000000"})  # $75B ⇒ approx 0.5% → ~$375M
    )

    snap = await market_feed.fetch_market_overview()

    assert snap["btc_price_usdt"] == pytest.approx(74180.0)
    assert snap["btc_change_24h"] == pytest.approx(-1.97)
    assert snap["fear_greed_index"] == 22
    assert snap["funding_rate_btc"] == pytest.approx(0.00010)
    assert snap["long_short_ratio"] == pytest.approx(1.69)
    # OI = openInterest (BTC) * BTC price
    assert snap["open_interest_usdt"] == pytest.approx(101234.5 * 74180.0)


@pytest.mark.asyncio
@respx.mock
async def test_market_overview_falls_back_when_apis_fail(monkeypatch):
    """All upstream failures → fallback stub values, no exception raised."""
    for k in market_feed._market_cache:
        market_feed._market_cache[k].value = None
        market_feed._market_cache[k].ts = 0.0

    respx.get("https://api.coingecko.com/api/v3/simple/price").mock(return_value=Response(500))
    respx.get("https://api.alternative.me/fng/").mock(return_value=Response(500))
    respx.get("https://fapi.binance.com/fapi/v1/openInterest").mock(return_value=Response(500))
    respx.get("https://fapi.binance.com/fapi/v1/premiumIndex").mock(return_value=Response(500))
    respx.get("https://fapi.binance.com/futures/data/topLongShortAccountRatio").mock(return_value=Response(500))
    respx.get("https://fapi.binance.com/fapi/v1/ticker/24hr").mock(return_value=Response(500))

    snap = await market_feed.fetch_market_overview()

    # Should match fallback defaults
    assert snap["btc_price_usdt"] == market_feed.FALLBACK["btc_price_usdt"]
    assert snap["fear_greed_index"] == market_feed.FALLBACK["fear_greed_index"]


@pytest.mark.asyncio
@respx.mock
async def test_news_returns_list_of_dicts():
    market_feed._news_cache.value = None
    market_feed._news_cache.ts = 0.0

    sample = {
        "results": [
            {
                "id": 999,
                "title": "BTC futures basis narrows",
                "url": "https://example.com/a",
                "source": {"title": "CryptoPanic", "domain": "cryptopanic.com"},
                "published_at": "2026-05-28T10:00:00Z",
                "currencies": [{"code": "BTC", "title": "Bitcoin"}],
            },
        ]
    }
    respx.get("https://cryptopanic.com/api/v1/posts/").mock(return_value=Response(200, json=sample))

    items = await market_feed.fetch_news(limit=5)
    assert len(items) == 1
    assert items[0]["title"] == "BTC futures basis narrows"
    assert "BTC" in items[0]["tags"]


@pytest.mark.asyncio
@respx.mock
async def test_news_returns_cached_on_failure():
    # Prime cache
    market_feed._news_cache.value = [{"id": "old", "title": "cached one", "tags": [],
                                       "url": None, "source": None,
                                       "published_at": "2026-05-28T00:00:00Z"}]
    market_feed._news_cache.ts = 0  # force refresh attempt

    respx.get("https://cryptopanic.com/api/v1/posts/").mock(return_value=Response(500))

    items = await market_feed.fetch_news(limit=5)
    # Upstream failed → fall back to last-good cache
    assert items and items[0]["title"] == "cached one"
