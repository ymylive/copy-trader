"""Async SQLAlchemy engine + session helpers."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import JSON, types
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# ── Cross-DB types ─────────────────────────────────────────────────────


class JSONB(types.TypeDecorator):
    """Use PG JSONB when available, fall back to JSON for SQLite/tests."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


class StringArray(types.TypeDecorator):
    """text[] on PG, JSON-encoded list on SQLite."""

    impl = types.JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY
            return dialect.type_descriptor(ARRAY(types.Text()))
        return dialect.type_descriptor(types.JSON())

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return [] if dialect.name == "postgresql" else json.dumps([])
        if dialect.name == "postgresql":
            return list(value)
        return json.dumps(list(value))

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return []
        if dialect.name == "postgresql":
            return list(value)
        if isinstance(value, str):
            try:
                return list(json.loads(value))
            except Exception:  # noqa: BLE001
                return []
        return list(value)


# ── Engine / Session ──────────────────────────────────────────────────


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        s = get_settings()
        connect_args: dict = {}
        # SQLite needs check_same_thread off in async use only when sync; here aiosqlite handles it.
        _engine = create_async_engine(
            s.effective_database_url,
            echo=s.db_echo,
            future=True,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db_for_tests() -> None:
    """Create all tables (used in pytest with SQLite)."""
    from app.db import models  # noqa: F401  ensure models registered

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_for_tests() -> None:
    from app.db import models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def reset_engine_for_tests() -> None:
    """Clear cached engine/session so a new DATABASE_URL takes effect."""
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None
