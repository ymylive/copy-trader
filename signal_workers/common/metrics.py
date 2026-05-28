"""Prometheus metric registry + HTTP exposer used by every worker.

Each worker process exposes its own ``/metrics`` endpoint on a port chosen
from the ``METRICS_PORT_<WORKER>`` env (with sane fallbacks below).
"""

from __future__ import annotations

import os

import structlog
from prometheus_client import Counter, Gauge, Histogram, start_http_server

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Cross-worker generic metrics
# ---------------------------------------------------------------------------
SIGNAL_EVENTS_TOTAL = Counter(
    "signal_events_total",
    "Total SignalEvents successfully published to Redis Streams.",
    labelnames=("source", "kind"),
)

BUS_DROPPED_TOTAL = Counter(
    "bus_dropped_total",
    "SignalEvents dropped by the EventBus (dedupe/ratelimit/redis_error).",
    labelnames=("source", "reason"),
)

EVENT_LAG_MS = Histogram(
    "event_lag_ms",
    "Upstream-event-timestamp → publish-time gap in ms.",
    labelnames=("source",),
    # Tuned for sub-second targets but with long tail for REST pollers.
    buckets=(10, 25, 50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000, 30_000),
)

# ---------------------------------------------------------------------------
# Hyperliquid WS-specific
# ---------------------------------------------------------------------------
WS_RECONNECTS_TOTAL = Counter(
    "ws_reconnects_total",
    "WebSocket reconnect attempts (any reason).",
    labelnames=("source", "endpoint"),
)
WS_ACTIVE_CONNECTIONS = Gauge(
    "ws_active_connections",
    "Currently open WebSocket connections.",
    labelnames=("source",),
)
WS_SUBSCRIPTIONS = Gauge(
    "ws_subscriptions",
    "Active per-trader subscriptions on each WS connection.",
    labelnames=("source",),
)

# ---------------------------------------------------------------------------
# OKX poll-specific
# ---------------------------------------------------------------------------
OKX_POLLS_TOTAL = Counter(
    "okx_polls_total",
    "OKX public-* REST polls performed.",
    labelnames=("endpoint", "status"),
)
OKX_ACTIVE_TRADERS = Gauge(
    "okx_active_traders",
    "OKX lead-traders being polled this tick.",
)

# ---------------------------------------------------------------------------
# EVM smart-money-specific
# ---------------------------------------------------------------------------
EVM_SUBSCRIBED_ADDRESSES = Gauge(
    "evm_subscribed_addresses",
    "Number of EOAs currently being watched for perp DEX activity.",
    labelnames=("chain",),
)
EVM_LOGS_TOTAL = Counter(
    "evm_logs_total",
    "Decoded perp-DEX logs observed.",
    labelnames=("chain", "contract", "event"),
)

# ---------------------------------------------------------------------------
# Default port table — workers can override via env.
# ---------------------------------------------------------------------------
_DEFAULT_PORTS = {
    "hyperliquid_ws": 9301,
    "okx_public": 9302,
    "evm_smart_money": 9303,
    "binance_lead": 9304,
    "bicoin_scraper": 9305,
}


def start_metrics_server(worker: str, port: int | None = None) -> int:
    """Bind ``prometheus_client`` HTTP exposer; return the actual port used.

    Picks port from (1) explicit arg, (2) ``METRICS_PORT_<WORKER>`` env,
    (3) the per-worker default table. Silently swallows ``OSError`` if the
    port is in use so unit tests can call this twice.
    """
    if port is None:
        env_key = f"METRICS_PORT_{worker.upper()}"
        port = int(os.environ.get(env_key, _DEFAULT_PORTS.get(worker, 9300)))
    try:
        start_http_server(port)
        log.info("metrics.server_started", worker=worker, port=port)
    except OSError as exc:
        log.warning("metrics.server_bind_failed", worker=worker, port=port, err=str(exc))
    return port
