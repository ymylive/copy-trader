"""Shared pytest fixtures.

We rely on pytest's ``rootdir`` mechanism (pyproject ``pythonpath``) to make
``import signal_workers`` resolve to the parent directory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make ``import signal_workers`` work by adding the *parent* of this dir to
# sys.path. We do it imperatively (rather than relying on pyproject pythonpath
# alone) so plain ``pytest`` invocations from any cwd still work.
HERE = Path(__file__).resolve().parent
SIGNAL_WORKERS_DIR = HERE.parent
PARENT = SIGNAL_WORKERS_DIR.parent

for p in (str(PARENT), str(SIGNAL_WORKERS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Ensure asyncio mode env is consistent.
os.environ.setdefault("LOG_LEVEL", "WARNING")
