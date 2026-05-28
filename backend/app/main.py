"""FastAPI entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api.v1 import api_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers


log = logging.getLogger(__name__)


# ── Prometheus metrics ───────────────────────────────────────────────
# Use a custom registry so reloading the module doesn't blow up on duplicates.
from prometheus_client import CollectorRegistry, REGISTRY


def _safe_counter(name: str, doc: str, labels: list[str]):
    try:
        return Counter(name, doc, labels)
    except ValueError:
        # Already registered (e.g. uvicorn reload). Re-fetch.
        return REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]


def _safe_histogram(name: str, doc: str, labels: list[str]):
    try:
        return Histogram(name, doc, labels)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]


REQ_COUNT = _safe_counter(
    "ct_http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
REQ_LATENCY = _safe_histogram(
    "ct_http_request_duration_seconds", "Request duration", ["method", "path"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """App lifespan: optional DB ping; start scheduler in non-test envs."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    log.info("startup app_env=%s db=%s", settings.app_env, settings.effective_database_url)

    if not settings.skip_db_startup_check:
        from app.db.base import get_engine
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.exec_driver_sql("SELECT 1")
            log.info("db connection ok")
        except Exception as exc:  # noqa: BLE001
            log.warning("db connection failed at startup: %s", exc)

    scheduler = None
    if settings.enable_scheduler:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.services.scheduler import register_jobs

        scheduler = AsyncIOScheduler(timezone="UTC")
        register_jobs(scheduler)
        scheduler.start()
        log.info("scheduler started with %s jobs", len(scheduler.get_jobs()))

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
        log.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.middleware("http")
    async def _metrics_middleware(request, call_next):  # type: ignore[override]
        import time as _t
        start = _t.perf_counter()
        response = await call_next(request)
        elapsed = _t.perf_counter() - start
        path = request.url.path
        # Avoid high-cardinality labels for IDs by collapsing /\d+/ → /:id/
        normalized = "/".join("{id}" if seg.isdigit() else seg for seg in path.split("/"))
        REQ_LATENCY.labels(request.method, normalized).observe(elapsed)
        REQ_COUNT.labels(request.method, normalized, str(response.status_code)).inc()
        return response

    @app.get("/healthz", response_class=PlainTextResponse, tags=["meta"])
    async def healthz() -> str:
        return "ok"

    @app.get("/metrics", tags=["meta"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {
            "service": settings.app_name,
            "version": "0.1.0",
            "api": settings.api_v1_prefix,
            "docs": "/docs",
        }

    return app


# Uvicorn entrypoint: `uvicorn app.main:app`
app = create_app()


if __name__ == "__main__":
    import os

    import uvicorn

    reload = os.environ.get("CT_RELOAD", "0") == "1"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        log_level="info",
    )
