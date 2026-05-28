"""OKX position-diff invariants — pure function, no network/IO."""

from __future__ import annotations

import time

from signal_workers.workers.okx_public.diff import build_snapshot_event, diff_positions


def _pos(*, sub_pos_id: str, inst: str, side: str, size: str, px: str = "65000", lev: str = "10"):
    return {
        "subPosId": sub_pos_id,
        "instId": inst,
        "posSide": side,
        "subPos": size,
        "openAvgPx": px,
        "markPx": px,
        "lever": lev,
        "margin": "1000",
        "upl": "0",
    }


NOW = int(time.time() * 1000)


def test_cold_start_emits_open_per_row() -> None:
    curr = [
        _pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="1.0"),
        _pos(sub_pos_id="B", inst="ETH-USDT-SWAP", side="short", size="2.0"),
    ]
    events = list(
        diff_positions(
            trader_id="trader-1",
            trader_name="alice",
            prev=None,
            curr=curr,
            ts_ms=NOW,
            received_ts_ms=NOW,
        )
    )
    assert len(events) == 2
    kinds = {e.kind for e in events}
    assert kinds == {"order_open"}
    assert {e.payload["symbol"] for e in events} == {"BTC-USDT-SWAP", "ETH-USDT-SWAP"}


def test_close_when_position_disappears() -> None:
    prev = [_pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="1.0")]
    events = list(
        diff_positions(
            trader_id="t",
            trader_name=None,
            prev=prev,
            curr=[],
            ts_ms=NOW,
            received_ts_ms=NOW,
        )
    )
    assert len(events) == 1
    assert events[0].kind == "order_close"
    assert events[0].payload["action"] == "close"
    assert events[0].payload["qty_delta"] == "1.0"


def test_increase_emits_open_with_delta() -> None:
    prev = [_pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="1.0")]
    curr = [_pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="3.0")]
    events = list(
        diff_positions(trader_id="t", trader_name=None, prev=prev, curr=curr, ts_ms=NOW, received_ts_ms=NOW)
    )
    assert len(events) == 1
    assert events[0].kind == "order_open"
    assert events[0].payload["action"] == "increase"
    assert events[0].payload["qty_delta"] == "2.0"


def test_reduce_emits_close_with_delta() -> None:
    prev = [_pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="3.0")]
    curr = [_pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="1.2")]
    events = list(
        diff_positions(trader_id="t", trader_name=None, prev=prev, curr=curr, ts_ms=NOW, received_ts_ms=NOW)
    )
    assert len(events) == 1
    assert events[0].kind == "order_close"
    assert events[0].payload["action"] == "reduce"
    assert events[0].payload["qty_delta"] == "1.8"


def test_no_change_no_events() -> None:
    p = [_pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="1.0")]
    events = list(
        diff_positions(trader_id="t", trader_name=None, prev=p, curr=p, ts_ms=NOW, received_ts_ms=NOW)
    )
    assert events == []


def test_snapshot_event_carries_all_rows() -> None:
    curr = [
        _pos(sub_pos_id="A", inst="BTC-USDT-SWAP", side="long", size="1.0"),
        _pos(sub_pos_id="B", inst="ETH-USDT-SWAP", side="short", size="2.0"),
    ]
    ev = build_snapshot_event(
        trader_id="trader-1",
        trader_name="alice",
        curr=curr,
        ts_ms=NOW,
        received_ts_ms=NOW,
    )
    assert ev.kind == "position_snapshot"
    assert len(ev.payload["positions"]) == 2
    sym = {r["symbol"] for r in ev.payload["positions"]}
    assert sym == {"BTC-USDT-SWAP", "ETH-USDT-SWAP"}


def test_diff_normalises_binance_symbol_format() -> None:
    """Even if OKX someday returns a BTCUSDT-shaped instId, normaliser saves us."""
    curr = [_pos(sub_pos_id="A", inst="BTCUSDT", side="long", size="1.0")]
    events = list(
        diff_positions(trader_id="t", trader_name=None, prev=None, curr=curr, ts_ms=NOW, received_ts_ms=NOW)
    )
    assert events[0].payload["symbol"] == "BTC-USDT-SWAP"
