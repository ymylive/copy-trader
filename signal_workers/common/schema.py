"""Pydantic v2 models for the unified ``SignalEvent`` envelope.

The schema is the single source of truth between :mod:`signal_workers` (producer)
and :mod:`execution_engine` (consumer); it mirrors ``docs/event_schema.md``.

Design points
-------------
* All numeric fields are kept as strings to avoid float drift across language
  / SDK boundaries — the execution side parses them with ``Decimal``.
* ``event_id`` is deterministically derived via :func:`make_event_id` so that
  consumers can dedupe even if a worker is restarted mid-stream.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Type aliases (intentionally narrow Literals so typos blow up at validation
# time rather than silently mis-routing events).
# ---------------------------------------------------------------------------
SignalSource = Literal[
    "hyperliquid",
    "okx_public",
    "binance_lead",
    "evm_smart_money",
    "okx_portfolio",
    "bicoin",
]

SignalKind = Literal[
    "position_snapshot",
    "order_open",
    "order_close",
    "order_modify",
    "margin_change",
]

Side = Literal["long", "short"]
Action = Literal["open", "increase", "reduce", "close"]


class PositionRow(BaseModel):
    """One leg of a position-snapshot payload.

    All amounts are decimal-strings so they survive JSON round-trips with no
    precision loss; execution_engine converts them to :class:`decimal.Decimal`.
    """

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Unified symbol, e.g. BTC-USDT-SWAP")
    side: Side
    qty: str
    entry_px: str
    lev: str = "1"
    margin: str = "0"
    unrealized_pnl: str = "0"


class TraderMeta(BaseModel):
    model_config = ConfigDict(extra="allow")  # let workers stuff source-specific stuff in

    exchange: Optional[str] = None
    is_hidden: Optional[bool] = None
    is_lead: Optional[bool] = None
    chain: Optional[str] = None  # for evm_smart_money


class SignalEvent(BaseModel):
    """The exact wire-format published to ``stream:signals:{source}:{trader_id}``.

    See ``docs/event_schema.md`` for the human-readable spec.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: Literal["signal.v1"] = Field(default="signal.v1", alias="schema")
    event_id: str
    source: SignalSource
    trader_id: str
    trader_name: Optional[str] = None
    trader_meta: TraderMeta = Field(default_factory=TraderMeta)
    ts: int = Field(..., description="event timestamp in ms (from upstream)")
    received_ts: int = Field(
        default_factory=lambda: int(time.time() * 1000),
        description="worker receive timestamp in ms (latency analysis)",
    )
    kind: SignalKind
    payload: dict[str, Any]
    # Optional trace id, propagated end-to-end via structlog.
    trace_id: Optional[str] = None

    @field_validator("ts", "received_ts")
    @classmethod
    def _ts_must_be_ms(cls, v: int) -> int:
        # 10^12 = year 2001 in ms, 10^15 = year 33658 — sanity range.
        if not (10**12 < v < 10**15):
            raise ValueError(f"ts must be ms-precision unix timestamp, got {v}")
        return v

    def to_redis_fields(self) -> dict[str, str]:
        """Flatten the event into the str→str map expected by ``XADD``.

        We serialise the payload as JSON (via ``orjson``) and keep the
        envelope fields top-level so consumers can do quick filtering
        without re-parsing JSON.
        """
        import orjson

        return {
            "schema": self.schema_version,
            "event_id": self.event_id,
            "source": self.source,
            "trader_id": self.trader_id,
            "trader_name": self.trader_name or "",
            "ts": str(self.ts),
            "received_ts": str(self.received_ts),
            "kind": self.kind,
            "payload": orjson.dumps(self.payload).decode("utf-8"),
            "trader_meta": orjson.dumps(self.trader_meta.model_dump(exclude_none=True)).decode("utf-8"),
            "trace_id": self.trace_id or "",
        }


# ---------------------------------------------------------------------------
# event_id generation
# ---------------------------------------------------------------------------
def make_event_id(
    *,
    source: str,
    trader_id: str,
    kind: str,
    ts: int,
    payload_key_fields: dict[str, Any] | None = None,
) -> str:
    """Deterministically derive an ``event_id`` for idempotent downstream dedupe.

    The contract is: any two SignalEvents that the *consumer* must treat as
    "the same business event" should hash to the same id. Workers therefore
    pick the *minimum* discriminating set of fields per kind:

    * ``order_open`` / ``order_close``: symbol + side + qty_delta + px
    * ``position_snapshot``: just ts at second precision (one bucket / sec)
    * ``margin_change``: margin_delta

    The ts is rounded to the nearest second to make a worker restart with a
    slightly-later receive-time still hash to the original id.
    """
    h = hashlib.sha256()
    h.update(source.encode())
    h.update(b"|")
    h.update(trader_id.encode())
    h.update(b"|")
    h.update(kind.encode())
    h.update(b"|")
    h.update(str(ts // 1000).encode())  # second-precision bucket
    if payload_key_fields:
        # Stable key order — sorted by key so dict iteration order does not
        # leak into the hash.
        for k in sorted(payload_key_fields):
            v = payload_key_fields[k]
            h.update(b"|")
            h.update(k.encode())
            h.update(b"=")
            h.update(str(v).encode())
    return h.hexdigest()[:32]
