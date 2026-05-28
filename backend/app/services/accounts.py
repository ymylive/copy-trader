"""Exchange-account service helpers."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.ip_pool import get_pool
from app.core.security import encrypt_secret
from app.db.models import ExchangeAccount, NavPoint, PositionSnapshot, User

log = logging.getLogger(__name__)


async def list_accounts(db: AsyncSession, user: User) -> Sequence[ExchangeAccount]:
    res = await db.execute(
        select(ExchangeAccount)
        .where(ExchangeAccount.user_id == user.id)
        .order_by(ExchangeAccount.created_at.asc())
    )
    return res.scalars().all()


async def get_account(db: AsyncSession, user: User, account_id: int) -> ExchangeAccount:
    acc = await db.get(ExchangeAccount, account_id)
    if acc is None or acc.user_id != user.id:
        raise NotFound("account not found", code="account_not_found")
    return acc


async def create_account(
    db: AsyncSession,
    user: User,
    *,
    alias: str,
    tier: str,
    exchange: str,
    leverage_default: int,
) -> ExchangeAccount:
    acc = ExchangeAccount(
        user_id=user.id,
        alias=alias,
        tier=tier,
        exchange=exchange,
        leverage_default=leverage_default,
        status="inactive",
        egress_ips=[],
    )
    db.add(acc)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise Conflict("alias already exists", code="alias_taken") from exc
    log.info("account.created id=%s user_id=%s exchange=%s", acc.id, user.id, exchange)
    return acc


async def update_account(
    db: AsyncSession,
    user: User,
    account_id: int,
    *,
    alias: Optional[str] = None,
    leverage_default: Optional[int] = None,
) -> ExchangeAccount:
    acc = await get_account(db, user, account_id)
    if alias is not None:
        acc.alias = alias
    if leverage_default is not None:
        acc.leverage_default = leverage_default
    acc.updated_at = datetime.utcnow()
    return acc


async def set_api_key(
    db: AsyncSession,
    user: User,
    account_id: int,
    *,
    api_key: str,
    api_secret: str,
    passphrase: Optional[str] = None,
    uid: Optional[str] = None,
) -> ExchangeAccount:
    acc = await get_account(db, user, account_id)
    acc.api_key_enc = encrypt_secret(api_key)
    acc.api_secret_enc = encrypt_secret(api_secret)
    acc.passphrase_enc = encrypt_secret(passphrase) if passphrase else None
    if uid:
        acc.uid = uid
    acc.updated_at = datetime.utcnow()
    log.info("account.api_key_set id=%s", acc.id)
    return acc


async def activate_account(db: AsyncSession, user: User, account_id: int) -> ExchangeAccount:
    acc = await get_account(db, user, account_id)
    if not acc.api_key_enc or not acc.api_secret_enc:
        raise BadRequest("API key/secret required before activation", code="api_key_missing")
    if not acc.egress_ips:
        acc.egress_ips = get_pool().allocate(1)
    acc.status = "active"
    acc.activated_at = datetime.utcnow()
    acc.updated_at = datetime.utcnow()
    # NOTE: execution_engine stub — would notify via Redis pubsub here.
    log.info("account.activated id=%s egress=%s", acc.id, acc.egress_ips)
    return acc


async def delete_account(db: AsyncSession, user: User, account_id: int) -> None:
    acc = await get_account(db, user, account_id)
    await db.delete(acc)
    log.info("account.deleted id=%s", account_id)


async def latest_positions(
    db: AsyncSession, account_id: int
) -> Sequence[PositionSnapshot]:
    # We define "latest frame" as the most recent ts for this account.
    res = await db.execute(
        select(PositionSnapshot.ts)
        .where(PositionSnapshot.exchange_account_id == account_id)
        .order_by(desc(PositionSnapshot.ts))
        .limit(1)
    )
    latest_ts = res.scalar_one_or_none()
    if latest_ts is None:
        return []
    rows = await db.execute(
        select(PositionSnapshot).where(
            PositionSnapshot.exchange_account_id == account_id,
            PositionSnapshot.ts == latest_ts,
        )
    )
    return rows.scalars().all()


async def nav_curve(
    db: AsyncSession,
    account_id: int,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 5000,
) -> Sequence[NavPoint]:
    stmt = select(NavPoint).where(NavPoint.exchange_account_id == account_id)
    if start:
        stmt = stmt.where(NavPoint.ts >= start)
    if end:
        stmt = stmt.where(NavPoint.ts <= end)
    stmt = stmt.order_by(NavPoint.ts.asc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
