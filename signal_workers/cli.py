"""``python -m signal_workers --worker <name>`` entry-point.

This is the single binary every k8s ``Deployment`` / docker-compose service
launches; the ``--worker`` flag picks which sub-module's ``run()`` coroutine
to await.  No business logic lives here — only argv parsing, signal handling
and the dispatch table.
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from typing import Awaitable, Callable

import structlog

from signal_workers.common.logging_setup import configure_logging
from signal_workers.common.metrics import start_metrics_server

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Dispatch table: worker name -> coroutine factory.
#
# Imports are *lazy* so that a missing optional dep in one worker (e.g.
# ``hyperliquid-python-sdk`` on Python 3.13) never prevents the other
# workers from starting.
# ---------------------------------------------------------------------------
WorkerFactory = Callable[[argparse.Namespace], Awaitable[None]]


def _load(modpath: str) -> WorkerFactory:
    """Return the ``run(args)`` coroutine of a worker module on demand."""

    def _factory(args: argparse.Namespace) -> Awaitable[None]:
        import importlib

        mod = importlib.import_module(modpath)
        return mod.run(args)

    return _factory


WORKERS: dict[str, WorkerFactory] = {
    "hyperliquid_ws": _load("signal_workers.workers.hyperliquid_ws.main"),
    "okx_public": _load("signal_workers.workers.okx_public.main"),
    "evm_smart_money": _load("signal_workers.workers.evm_smart_money.main"),
    "binance_lead": _load("signal_workers.workers.binance_lead.main"),
    "bicoin_scraper": _load("signal_workers.workers.bicoin_scraper.main"),
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="signal_workers",
        description="Copy Trader signal acquisition daemon.",
    )
    p.add_argument(
        "--worker",
        required=True,
        choices=sorted(WORKERS),
        help="Which signal worker to launch.",
    )
    p.add_argument(
        "--redis-url",
        default=None,
        help="redis:// URL (falls back to REDIS_URL env, then redis://localhost:6379/0).",
    )
    p.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL DSN for trader registry (falls back to DATABASE_URL env).",
    )
    p.add_argument(
        "--metrics-port",
        type=int,
        default=None,
        help="Override Prometheus exposer port (default per-worker, see common/metrics.py).",
    )
    p.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, the worker emits events to stdout instead of Redis.",
    )
    return p


async def _amain(args: argparse.Namespace) -> int:
    """Async entry-point.  Wires up signals, metrics, then awaits the worker."""
    factory = WORKERS[args.worker]
    coro = factory(args)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_signal(signame: str) -> None:
        log.info("shutdown.signal_received", signal=signame)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal, sig.name)
        except NotImplementedError:
            # Windows / non-asyncio platforms: best-effort fallback.
            signal.signal(sig, lambda *_: stop_event.set())

    # The worker coroutine is expected to read ``args.stop_event`` if set —
    # we attach it dynamically rather than mutating its signature.
    args.stop_event = stop_event  # type: ignore[attr-defined]

    worker_task = asyncio.create_task(coro, name=f"worker.{args.worker}")
    stop_task = asyncio.create_task(stop_event.wait(), name="shutdown.waiter")

    done, pending = await asyncio.wait(
        {worker_task, stop_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    # If the user asked to stop, cancel the worker and give it time to clean up.
    if stop_task in done and not worker_task.done():
        log.info("shutdown.cancelling_worker")
        worker_task.cancel()
        try:
            await asyncio.wait_for(worker_task, timeout=10)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    # Re-raise worker errors so the process exits with non-zero on crash.
    if worker_task.done() and not worker_task.cancelled():
        exc = worker_task.exception()
        if exc is not None:
            log.error("worker.crashed", err=str(exc), exc_info=exc)
            return 1
    for t in pending:
        t.cancel()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    configure_logging(worker=args.worker, level=args.log_level)
    start_metrics_server(args.worker, port=args.metrics_port)

    try:
        return asyncio.run(_amain(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
