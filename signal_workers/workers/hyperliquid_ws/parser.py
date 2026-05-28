"""Pure functions that decode Hyperliquid WS frames into :class:`SignalEvent`.

Kept in its own module (no asyncio, no redis, no network) so it can be unit
tested with hand-crafted JSON samples — see ``tests/test_hyperliquid_parser.py``.

Reference frames (see ``research/signal_sources_research.md`` §3.2):

* ``userEvents`` — fills + funding + liquidation + nonUserCancel
* ``userFills``  — fills only (``isSnapshot`` first frame)
* ``webData2``   — large aggregate snapshot (positions + open orders + balance)
"""

from __future__ import annotations

import time
from typing import Any, Iterator

from signal_workers.common.normalizer import normalize_side, normalize_symbol
from signal_workers.common.schema import PositionRow, SignalEvent, make_event_id


def _now_ms() -> int:
    return int(time.time() * 1000)


# ---------------------------------------------------------------------------
# userEvents / userFills  → order_open / order_close
# ---------------------------------------------------------------------------
def parse_user_fill(fill: dict[str, Any], trader_id: str) -> SignalEvent | None:
    """Convert one element of ``userEvents.fills[]`` / ``userFills.fills[]`` to
    a ``SignalEvent``.

    Hyperliquid's fill schema (from the SDK reference)::

        { "coin": "BTC", "px": "65000.0", "sz": "0.5", "side": "B"|"A",
          "time": 1714286400000, "startPosition": "...", "dir": "Open Long",
          "closedPnl": "0.0", "hash": "0x...", "oid": 12345, "crossed": true,
          "fee": "...", "tid": ..., "feeToken": "USDC" }

    The ``dir`` field tells us whether this fill opened or closed a position
    ("Open Long", "Close Long", "Open Short", "Close Short", "Buy", "Sell" for
    spot which we ignore).
    """
    try:
        coin = fill["coin"]
        px = str(fill["px"])
        sz = str(fill["sz"])
        side_raw = fill["side"]  # "B" or "A"
        ts = int(fill["time"])
        direction = fill.get("dir", "")
    except (KeyError, TypeError, ValueError):
        return None

    # Map the trade-direction string to (action, side) for the SignalEvent.
    direction_low = direction.lower()
    if "open" in direction_low:
        action = "open"
    elif "close" in direction_low:
        action = "close"
    elif "long>short" in direction_low or "short>long" in direction_low:
        # Hedged flip — treat as "close" then "open"; we emit one event of
        # the new side opening (the close half lands in startPosition→0).
        action = "open"
    else:
        # Unknown directive (spot? funding?). Skip.
        return None

    # Pick the *resulting* side, not the order direction.
    # "Open Long" / "Close Short" → resulting long position
    # "Open Short" / "Close Long" → resulting short position
    if "long" in direction_low:
        side = "long"
    elif "short" in direction_low:
        side = "short"
    else:
        # Bare "Buy"/"Sell" — fall back to side_raw mapping.
        side = normalize_side(side_raw == "B")

    symbol = normalize_symbol(coin, source="hyperliquid")
    kind = "order_open" if action in ("open",) else "order_close"

    payload = {
        "symbol": symbol,
        "side": side,
        "action": action,
        "qty_delta": sz,
        "px": px,
        "reason": "liquidation" if fill.get("liquidation") else "manual",
    }

    return SignalEvent(
        event_id=make_event_id(
            source="hyperliquid",
            trader_id=trader_id,
            kind=kind,
            ts=ts,
            payload_key_fields={
                "symbol": symbol,
                "side": side,
                "action": action,
                "qty_delta": sz,
                "px": px,
                "oid": fill.get("oid", ""),
            },
        ),
        source="hyperliquid",
        trader_id=trader_id,
        ts=ts,
        received_ts=_now_ms(),
        kind=kind,
        payload=payload,
    )


def parse_user_events_frame(frame: dict[str, Any], trader_id: str) -> Iterator[SignalEvent]:
    """Iterate fills carried inside a ``userEvents`` push frame.

    Hyperliquid wraps the actual data in either ``frame["data"]`` (most
    subscriptions) or ``frame["data"]["fills"]`` (userEvents). We accept both
    shapes defensively.
    """
    data = frame.get("data", frame)

    fills: list[dict[str, Any]] = []
    if isinstance(data, dict):
        fills = data.get("fills") or []
    elif isinstance(data, list):
        fills = data

    for f in fills:
        ev = parse_user_fill(f, trader_id)
        if ev is not None:
            yield ev


# ---------------------------------------------------------------------------
# webData2  → position_snapshot
# ---------------------------------------------------------------------------
def parse_web_data2(frame: dict[str, Any], trader_id: str) -> SignalEvent | None:
    """Extract ``clearinghouseState.assetPositions[]`` from a webData2 push.

    ``webData2`` is the heaviest message Hyperliquid emits but it has the
    nicest single-shot semantics: one frame ≈ one full account state.
    """
    data = frame.get("data", frame)
    if not isinstance(data, dict):
        return None

    chs = data.get("clearinghouseState") or data.get("user_state") or {}
    asset_positions = chs.get("assetPositions") or []
    if not asset_positions and "positions" not in data:
        # No positions and no explicit empty array — skip rather than emit a
        # spurious "all closed" snapshot.
        return None

    rows: list[PositionRow] = []
    for ap in asset_positions:
        pos = ap.get("position") or ap
        try:
            coin = pos["coin"]
            szi = float(pos["szi"])
            entry = pos.get("entryPx") or "0"
            lev_obj = pos.get("leverage") or {}
            lev = str(lev_obj.get("value", lev_obj) if isinstance(lev_obj, dict) else lev_obj)
            margin = str(pos.get("marginUsed", "0"))
            upnl = str(pos.get("unrealizedPnl", "0"))
        except (KeyError, TypeError, ValueError):
            continue

        if szi == 0:
            continue

        rows.append(
            PositionRow(
                symbol=normalize_symbol(coin, source="hyperliquid"),
                side="long" if szi > 0 else "short",
                qty=str(abs(szi)),
                entry_px=str(entry),
                lev=lev,
                margin=margin,
                unrealized_pnl=upnl,
            )
        )

    ts = int(data.get("serverTime") or _now_ms())
    payload = {"positions": [r.model_dump() for r in rows]}

    return SignalEvent(
        event_id=make_event_id(
            source="hyperliquid",
            trader_id=trader_id,
            kind="position_snapshot",
            ts=ts,
            payload_key_fields={"n": len(rows)},
        ),
        source="hyperliquid",
        trader_id=trader_id,
        ts=ts,
        received_ts=_now_ms(),
        kind="position_snapshot",
        payload=payload,
    )
