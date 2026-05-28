"""Auth endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.deps import client_ip, get_current_user, get_db, user_agent
from app.db.models import User
from app.schemas.auth import (
    LoginIn,
    PasswordChangeIn,
    RegisterIn,
    TokenOut,
    UserOut,
)
from app.schemas.common import MessageOut
from app.services import users as user_svc

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = await user_svc.register_user(
        db,
        username=payload.username,
        password=payload.password,
        email=payload.email,
        phone=payload.phone,
        invite_code=payload.invite_code,
    )
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    user, access, refresh = await user_svc.login(
        db,
        username=payload.username,
        password=payload.password,
        ip=client_ip(request),
        ua=user_agent(request),
    )
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=get_settings().access_token_ttl_min * 60,
    )


@router.post("/logout", response_model=MessageOut)
async def logout(_user: User = Depends(get_current_user)) -> MessageOut:
    # Stateless JWT — frontend just discards the token. (Blocklist could be
    # added later via Redis if needed.)
    return MessageOut(message="logged_out")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.post("/password", response_model=MessageOut)
async def change_password(
    payload: PasswordChangeIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    await user_svc.change_password(
        db,
        user=current_user,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )
    return MessageOut(message="password_changed")
