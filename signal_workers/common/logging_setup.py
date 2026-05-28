"""Structlog bootstrap shared across all workers.

Worker entry-points call :func:`configure_logging` exactly once at startup,
then use ``structlog.get_logger(__name__)`` everywhere else.
"""

from __future__ import annotations

import logging
import os
import sys

import structlog


def configure_logging(worker: str | None = None, level: str | None = None) -> None:
    log_level_name = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # stdlib logger sink (so 3rd-party libs flow through us too).
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    chain = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    # In production we want JSON; for local dev tty, pretty print.
    if sys.stdout.isatty() and os.environ.get("LOG_FORMAT", "").lower() != "json":
        chain.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        chain.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=chain,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    if worker:
        structlog.contextvars.bind_contextvars(worker=worker)
