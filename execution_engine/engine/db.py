"""Async SQLAlchemy engine + session helpers (standalone, no backend import)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings
from .models import Base

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        s = get_settings()
        _engine = create_async_engine(
            s.effective_database_url,
            future=True,
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
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_for_tests() -> None:
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def reset_engine_for_tests() -> None:
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None
