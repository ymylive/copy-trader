"""Egress IP pool allocator.

For the M0 milestone this is an in-memory stub. In production the pool will
be backed by Redis and managed by the execution_engine; we just hand out an
IP from a finite pool, falling back to round-robin when exhausted.
"""
from __future__ import annotations

import itertools
import threading
from typing import Iterable

from app.config import get_settings


class IPPool:
    def __init__(self, ips: Iterable[str]) -> None:
        self._ips = list(ips)
        self._cycle = itertools.cycle(self._ips) if self._ips else None
        self._lock = threading.Lock()

    def allocate(self, n: int = 1) -> list[str]:
        if not self._cycle:
            return []
        with self._lock:
            return [next(self._cycle) for _ in range(n)]


_pool: IPPool | None = None


def get_pool() -> IPPool:
    global _pool
    if _pool is None:
        _pool = IPPool(get_settings().egress_ip_pool)
    return _pool
