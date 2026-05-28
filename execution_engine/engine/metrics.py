"""Prometheus metrics for the execution engine."""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# ── Signal pipeline ────────────────────────────────────────────────────
signals_consumed = Counter(
    "engine_signals_consumed_total",
    "Signals consumed from redis streams",
    labelnames=("source", "kind"),
)
signals_skipped = Counter(
    "engine_signals_skipped_total",
    "Signals skipped (filter/dedup/risk)",
    labelnames=("reason",),
)

# ── Orders ─────────────────────────────────────────────────────────────
orders_submitted = Counter(
    "engine_orders_submitted_total",
    "Orders submitted to exchanges",
    labelnames=("exchange", "side", "kind"),
)
orders_failed = Counter(
    "engine_orders_failed_total",
    "Orders that failed",
    labelnames=("exchange", "reason"),
)
order_latency = Histogram(
    "engine_order_latency_seconds",
    "Order submission latency",
    labelnames=("exchange",),
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# ── Runners ────────────────────────────────────────────────────────────
runners_active = Gauge(
    "engine_runners_active",
    "Active follower runner coroutines",
)
runner_state = Gauge(
    "engine_runner_state",
    "Runner state (1=running 0.5=paused 0=stopped)",
    labelnames=("config_id",),
)

# ── Risk ───────────────────────────────────────────────────────────────
risk_triggers = Counter(
    "engine_risk_triggers_total",
    "Risk-rule triggers",
    labelnames=("rule",),
)
