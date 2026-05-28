"""FastAPI dependency injection helpers."""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Unauthorized
from app.core.security import decode_token
from app.db.base import get_sessionmaker
from app.db.models import User


bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async DB session, committing on success."""
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise Unauthorized("missing bearer token")
    try:
        payload = decode_token(creds.credentials)
    except ValueError as exc:
        raise Unauthorized(str(exc)) from exc
    if payload.get("typ") != "access":
        raise Unauthorized("not an access token")
    sub = payload.get("sub")
    if not sub:
        raise Unauthorized("malformed token: no sub")
    try:
        uid = int(sub)
    except (TypeError, ValueError) as exc:
        raise Unauthorized("malformed token: bad sub") from exc
    user = await db.get(User, uid)
    if user is None:
        raise Unauthorized("user not found")
    # Stash on request for easy access
    request.state.user = user
    return user


def client_ip(request: Request) -> str | None:
    """Best-effort client IP extraction."""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")
