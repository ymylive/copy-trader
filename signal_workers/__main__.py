"""Allow ``python -m signal_workers --worker <name>`` invocation."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
