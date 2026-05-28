"""Schema-level invariants — no network, no async."""

from __future__ import annotations

import time

import orjson
import pytest
from pydantic import ValidationError

from signal_workers.common.normalizer import normalize_side, normalize_symbol
from signal_workers.common.schema import (
    PositionRow,
    SignalEvent,
    make_event_id,
)


def _now_ms() -> int:
    return int(time.time() * 1000)


def test_signal_event_round_trip() -> None:
    """Construct → ``to_redis_fields`` → re-parse stays lossless."""
    ev = SignalEvent(
        event_id="abc",
        source="hyperliquid",
        trader_id="0xdead",
        ts=_now_ms(),
        kind="order_open",
        payload={"symbol": "BTC-USDT-SWAP", "side": "long", "action": "open"},
    )
    fields = ev.to_redis_fields()
    assert fields["source"] == "hyperliquid"
    assert fields["kind"] == "order_open"
    payload_back = orjson.loads(fields["payload"])
    assert payload_back["symbol"] == "BTC-USDT-SWAP"


def test_invalid_source_rejected() -> None:
    with pytest.raises(ValidationError):
        SignalEvent(
            event_id="x",
            source="totally_made_up",  # type: ignore[arg-type]
            trader_id="z",
            ts=_now_ms(),
            kind="order_open",
            payload={},
        )


def test_ts_must_be_ms_precision() -> None:
    with pytest.raises(ValidationError):
        SignalEvent(
            event_id="x",
            source="hyperliquid",
            trader_id="z",
            ts=1714286400,  # seconds, not ms
            kind="order_open",
            payload={},
        )


def test_event_id_deterministic() -> None:
    """Same inputs ⇒ same event_id (idempotency contract)."""
    a = make_event_id(
        source="hyperliquid",
        trader_id="0xdead",
        kind="order_open",
        ts=1714286400123,
        payload_key_fields={"symbol": "BTC-USDT-SWAP", "side": "long", "qty_delta": "0.5"},
    )
    b = make_event_id(
        source="hyperliquid",
        trader_id="0xdead",
        kind="order_open",
        ts=1714286400500,  # same second bucket → same id
        payload_key_fields={"symbol": "BTC-USDT-SWAP", "side": "long", "qty_delta": "0.5"},
    )
    assert a == b


def test_event_id_distinct_on_payload_change() -> None:
    a = make_event_id(
        source="hyperliquid",
        trader_id="0xdead",
        kind="order_open",
        ts=1714286400000,
        payload_key_fields={"symbol": "BTC-USDT-SWAP", "qty_delta": "0.5"},
    )
    b = make_event_id(
        source="hyperliquid",
        trader_id="0xdead",
        kind="order_open",
        ts=1714286400000,
        payload_key_fields={"symbol": "BTC-USDT-SWAP", "qty_delta": "1.0"},
    )
    assert a != b


def test_position_row_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        PositionRow(
            symbol="BTC-USDT-SWAP",
            side="long",
            qty="1",
            entry_px="65000",
            bogus_field="nope",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# normalizer
# ---------------------------------------------------------------------------
def test_normalize_symbol_binance() -> None:
    assert normalize_symbol("BTCUSDT", source="binance_lead") == "BTC-USDT-SWAP"
    assert normalize_symbol("ETHUSDC", source="binance_lead") == "ETH-USDT-SWAP"


def test_normalize_symbol_hyperliquid_overrides() -> None:
    assert normalize_symbol("BTC", source="hyperliquid") == "BTC-USDT-SWAP"
    assert normalize_symbol("kPEPE", source="hyperliquid") == "1000PEPE-USDT-SWAP"


def test_normalize_symbol_okx_passthrough() -> None:
    assert normalize_symbol("BTC-USDT-SWAP", source="okx_public") == "BTC-USDT-SWAP"


def test_normalize_side_variants() -> None:
    assert normalize_side("Buy") == "long"
    assert normalize_side("B") == "long"
    assert normalize_side("sell") == "short"
    assert normalize_side("A") == "short"
    assert normalize_side(1.5) == "long"
    assert normalize_side(-0.3) == "short"
    assert normalize_side(True) == "long"


def test_normalize_side_unknown_raises() -> None:
    with pytest.raises(ValueError):
        normalize_side("flat")
    with pytest.raises(ValueError):
        normalize_side(0)
