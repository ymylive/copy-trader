"""Pydantic v2 models for the SignalEvent v1 schema.

See ``docs/event_schema.md`` for the wire format.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

SignalKind = Literal[
    "position_snapshot",
    "order_open",
    "order_close",
    "order_modify",
    "margin_change",
]

SideLit = Literal["long", "short"]


class PositionItem(BaseModel):
    """One leg of a position_snapshot payload."""

    model_config = ConfigDict(extra="ignore")

    symbol: str
    side: SideLit
    qty: Decimal
    entry_px: Decimal
    lev: Optional[Decimal] = None
    margin: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = Field(default=None, alias="unrealized_pnl")

    @field_validator("qty", "entry_px", "lev", "margin", "unrealized_pnl", mode="before")
    @classmethod
    def _to_decimal(cls, v: Any) -> Any:
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class SignalEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_: str = Field(default="signal.v1", alias="schema")
    event_id: str
    source: str
    trader_id: str
    trader_name: Optional[str] = None
    trader_meta: dict[str, Any] = Field(default_factory=dict)
    ts: int
    received_ts: Optional[int] = None
    kind: SignalKind
    payload: dict[str, Any] = Field(default_factory=dict)

    # ── Convenience accessors (validated lazily) ────────────────────────
    def positions(self) -> list[PositionItem]:
        raw = self.payload.get("positions") or []
        return [PositionItem.model_validate(x) for x in raw]

    @property
    def symbol(self) -> Optional[str]:
        return self.payload.get("symbol")

    @property
    def side(self) -> Optional[str]:
        return self.payload.get("side")

    @property
    def action(self) -> Optional[str]:
        return self.payload.get("action")

    @property
    def qty_delta(self) -> Optional[Decimal]:
        v = self.payload.get("qty_delta")
        return Decimal(str(v)) if v is not None else None

    @property
    def px(self) -> Optional[Decimal]:
        v = self.payload.get("px")
        return Decimal(str(v)) if v is not None else None
