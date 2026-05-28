"""Hyperliquid real-time WebSocket worker.

See ``main.py`` for the entry-point; this file only re-exports it so
``python -m signal_workers.workers.hyperliquid_ws`` also works.
"""

from . import main as main  # re-export
