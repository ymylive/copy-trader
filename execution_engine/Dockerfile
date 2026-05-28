FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (needed by cryptography & ccxt)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY engine /app/engine
COPY main.py /app/main.py

RUN pip install -e .

# Prometheus metrics
EXPOSE 9100

CMD ["python", "main.py"]
