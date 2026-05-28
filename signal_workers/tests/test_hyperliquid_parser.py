"""Parser tests using hand-crafted Hyperliquid WS sample frames.

Sample frame shapes are taken from the official docs:
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
"""

from __future__ import annotations

from signal_workers.workers.hyperliquid_ws.parser import (
    parse_user_events_frame,
    parse_user_fill,
    parse_web_data2,
)

ADDR = "0xabc0000000000000000000000000000000000001"


def _fill(**over):
    base = {
        "coin": "BTC",
        "px": "65000.0",
        "sz": "0.5",
        "side": "B",
        "time": 1714286400000,
        "startPosition": "0.0",
        "dir": "Open Long",
        "closedPnl": "0",
        "hash": "0xabc",
        "oid": 12345,
        "crossed": True,
        "fee": "10.0",
        "tid": 1,
        "feeToken": "USDC",
    }
    base.update(over)
    return base


def test_parse_user_fill_open_long() -> None:
    ev = parse_user_fill(_fill(), trader_id=ADDR)
    assert ev is not None
    assert ev.kind == "order_open"
    assert ev.source == "hyperliquid"
    assert ev.trader_id == ADDR
    assert ev.payload["symbol"] == "BTC-USDT-SWAP"
    assert ev.payload["side"] == "long"
    assert ev.payload["action"] == "open"
    assert ev.payload["qty_delta"] == "0.5"
    assert ev.payload["px"] == "65000.0"


def test_parse_user_fill_close_short() -> None:
    ev = parse_user_fill(_fill(dir="Close Short", side="B"), trader_id=ADDR)
    assert ev is not None
    assert ev.kind == "order_close"
    assert ev.payload["action"] == "close"
    assert ev.payload["side"] == "short"


def test_parse_user_fill_kpepe_remap() -> None:
    ev = parse_user_fill(_fill(coin="kPEPE"), trader_id=ADDR)
    assert ev is not None
    assert ev.payload["symbol"] == "1000PEPE-USDT-SWAP"


def test_parse_user_fill_ignores_spot() -> None:
    # "Buy"/"Sell" on a spot pair has no "Open Long" hint — we skip rather
    # than risk emitting a bad perp event.
    ev = parse_user_fill(_fill(dir="Buy"), trader_id=ADDR)
    assert ev is None


def test_parse_user_fill_malformed() -> None:
    assert parse_user_fill({"coin": "BTC"}, trader_id=ADDR) is None
    assert parse_user_fill({}, trader_id=ADDR) is None


def test_parse_user_events_frame_yields_all_fills() -> None:
    frame = {
        "channel": "userEvents",
        "data": {
            "user": ADDR,
            "fills": [
                _fill(),
                _fill(coin="ETH", dir="Open Short", side="A", sz="2.0", px="3500.0"),
            ],
        },
    }
    events = list(parse_user_events_frame(frame, trader_id=ADDR))
    assert len(events) == 2
    assert events[0].payload["side"] == "long"
    assert events[1].payload["side"] == "short"
    assert events[1].payload["symbol"] == "ETH-USDT-SWAP"


def test_parse_web_data2_snapshot() -> None:
    frame = {
        "channel": "webData2",
        "data": {
            "user": ADDR,
            "serverTime": 1714286400000,
            "clearinghouseState": {
                "assetPositions": [
                    {
                        "position": {
                            "coin": "BTC",
                            "szi": "1.5",
                            "entryPx": "60000",
                            "leverage": {"value": 10},
                            "marginUsed": "9000",
                            "unrealizedPnl": "150",
                        }
                    },
                    {
                        "position": {
                            "coin": "ETH",
                            "szi": "-3.0",
                            "entryPx": "3000",
                            "leverage": {"value": 5},
                            "marginUsed": "1800",
                            "unrealizedPnl": "-50",
                        }
                    },
                ]
            },
        },
    }
    ev = parse_web_data2(frame, trader_id=ADDR)
    assert ev is not None
    assert ev.kind == "position_snapshot"
    rows = ev.payload["positions"]
    assert len(rows) == 2

    btc = next(r for r in rows if r["symbol"] == "BTC-USDT-SWAP")
    assert btc["side"] == "long"
    assert btc["qty"] == "1.5"
    assert btc["lev"] == "10"

    eth = next(r for r in rows if r["symbol"] == "ETH-USDT-SWAP")
    assert eth["side"] == "short"
    assert eth["qty"] == "3.0"


def test_parse_web_data2_empty() -> None:
    frame = {"channel": "webData2", "data": {"user": ADDR}}
    assert parse_web_data2(frame, trader_id=ADDR) is None
