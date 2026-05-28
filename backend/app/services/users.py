"""User registration / login service logic."""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, Unauthorized
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_invite_code,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.db.models import LoginHistory, ReferralRecord, User, WalletBalance

log = logging.getLogger(__name__)


async def _generate_unique_invite_code(db: AsyncSession) -> str:
    """Generate an 8-char invite code that is not already taken."""
    for _ in range(20):
        code = generate_invite_code(8)
        existing = await db.scalar(select(User).where(User.invite_code == code))
        if existing is None:
            return code
    raise RuntimeError("could not allocate invite_code")


async def register_user(
    db: AsyncSession,
    *,
    username: str,
    password: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    invite_code: Optional[str] = None,
) -> User:
    """Create a new user, optionally tagging the inviter."""
    existing = await db.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise Conflict("username already taken", code="username_taken")

    inviter_id: Optional[int] = None
    if invite_code:
        inviter = await db.scalar(select(User).where(User.invite_code == invite_code))
        if inviter is None:
            raise BadRequest("invalid invite code", code="invalid_invite_code")
        inviter_id = inviter.id

    new_code = await _generate_unique_invite_code(db)
    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        phone=phone,
        invite_code=new_code,
        referred_by=inviter_id,
        level=0,
        referral_rate=Decimal("0.10"),
    )
    db.add(user)
    await db.flush()  # populate id

    # ensure wallet row exists
    db.add(WalletBalance(user_id=user.id, currency="USDT", amount=Decimal("0")))

    # write referral record (pending until inviter sees first paid action)
    if inviter_id is not None:
        db.add(
            ReferralRecord(
                inviter_id=inviter_id,
                invitee_id=user.id,
                paid_amount=Decimal("0"),
                commission=Decimal("0"),
                status="pending",
            )
        )

    log.info("user.registered id=%s username=%s invited_by=%s", user.id, username, inviter_id)
    return user


async def login(
    db: AsyncSession,
    *,
    username: str,
    password: str,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> tuple[User, str, str]:
    """Verify credentials; return (user, access_token, refresh_token)."""
    user = await db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise Unauthorized("invalid credentials", code="invalid_credentials")

    access = create_access_token(str(user.id), extra={"username": user.username})
    refresh = create_refresh_token(str(user.id))

    db.add(LoginHistory(user_id=user.id, ip=ip, ua=ua))
    log.info("user.login id=%s ip=%s", user.id, ip)
    return user, access, refresh


async def change_password(
    db: AsyncSession, *, user: User, old_password: str, new_password: str
) -> None:
    if not verify_password(old_password, user.password_hash):
        raise Unauthorized("old password mismatch", code="bad_old_password")
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    log.info("user.password_changed id=%s", user.id)


def access_token_for(user: User) -> tuple[str, str, int]:
    """Mint a fresh access/refresh pair for an existing user."""
    s = get_settings()
    return (
        create_access_token(str(user.id), extra={"username": user.username}),
        create_refresh_token(str(user.id)),
        s.access_token_ttl_min * 60,
    )
