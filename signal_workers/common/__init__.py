"""Shared building blocks for every signal worker."""

from .schema import (
    SignalEvent,
    SignalKind,
    SignalSource,
    PositionRow,
    make_event_id,
)
from .event_bus import EventBus
from .normalizer import normalize_symbol, normalize_side
from .ratelimit import TokenBucket
from .metrics import (
    SIGNAL_EVENTS_TOTAL,
    WS_RECONNECTS_TOTAL,
    OKX_POLLS_TOTAL,
    OKX_ACTIVE_TRADERS,
    EVM_SUBSCRIBED_ADDRESSES,
    EVM_LOGS_TOTAL,
    EVENT_LAG_MS,
    BUS_DROPPED_TOTAL,
    start_metrics_server,
)
from .trader_registry import TraderRegistry, TraderRow

__all__ = [
    "SignalEvent",
    "SignalKind",
    "SignalSource",
    "PositionRow",
    "make_event_id",
    "EventBus",
    "normalize_symbol",
    "normalize_side",
    "TokenBucket",
    "SIGNAL_EVENTS_TOTAL",
    "WS_RECONNECTS_TOTAL",
    "OKX_POLLS_TOTAL",
    "OKX_ACTIVE_TRADERS",
    "EVM_SUBSCRIBED_ADDRESSES",
    "EVM_LOGS_TOTAL",
    "EVENT_LAG_MS",
    "BUS_DROPPED_TOTAL",
    "start_metrics_server",
    "TraderRegistry",
    "TraderRow",
]
