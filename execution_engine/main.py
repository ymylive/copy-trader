"""Process entrypoint for the execution engine.

Run with::

    python main.py
"""
from __future__ import annotations

import asyncio
import signal
import sys

from prometheus_client import start_http_server

from engine.config import get_settings
from engine.follower import FollowerEngine
from engine.logging_setup import get_logger, setup_logging
from engine.scheduler import EngineScheduler


async def amain() -> int:
    setup_logging()
    log = get_logger("main")
    settings = get_settings()
    log.info(
        "engine_boot",
        env=settings.app_env,
        instance=settings.instance_id,
        dry_run=settings.dry_run,
        metrics_port=settings.metrics_port,
    )

    # Prometheus exporter
    try:
        start_http_server(settings.metrics_port)
        log.info("metrics_started", port=settings.metrics_port)
    except OSError as exc:
        log.warning("metrics_port_in_use", error=str(exc))

    engine = FollowerEngine()
    sched = EngineScheduler(engine)
    await engine.start()
    sched.start()

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        log.info("signal_received_stopping")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # signal handlers not available on this platform (e.g. Windows event loop)
            pass

    try:
        await stop_event.wait()
    finally:
        log.info("shutting_down")
        await sched.shutdown()
        await engine.stop()
        log.info("shutdown_complete")
    return 0


def main() -> int:
    try:
        return asyncio.run(amain())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
