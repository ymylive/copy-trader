FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps needed by web3 (cytoolz) and asyncpg.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the package directory (the build context should be the repo root
# so this resolves; if you build from inside signal_workers/, change to `.`)
COPY signal_workers/ /app/signal_workers/

# Install the package in editable mode so logs map back to readable paths.
RUN pip install -e /app/signal_workers

# Default to the OKX worker — override with `--worker hyperliquid_ws` etc.
ENV WORKER=okx_public
EXPOSE 9300-9310

ENTRYPOINT ["python", "-m", "signal_workers"]
CMD ["--worker", "okx_public"]
