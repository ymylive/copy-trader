"""System / notify-channel / update endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.exceptions import Conflict, NotFound
from app.deps import get_current_user, get_db
from app.db.models import ExchangeAccount, NotificationLog, NotifyChannel, User
from app.schemas.common import MessageOut
from app.schemas.system import NotifyChannelIn, NotifyChannelOut, UpdateInfoOut

router = APIRouter()


@router.get("/notify-channels", response_model=List[NotifyChannelOut])
async def list_channels(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[NotifyChannelOut]:
    rows = await db.execute(
        select(NotifyChannel).where(NotifyChannel.user_id == user.id)
    )
    return [NotifyChannelOut.model_validate(c) for c in rows.scalars()]


@router.post(
    "/notify-channels", response_model=NotifyChannelOut, status_code=status.HTTP_201_CREATED
)
async def upsert_channel(
    payload: NotifyChannelIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotifyChannelOut:
    existing = await db.scalar(
        select(NotifyChannel).where(
            NotifyChannel.user_id == user.id, NotifyChannel.channel == payload.channel
        )
    )
    if existing is not None:
        existing.target = payload.target
        existing.enabled = payload.enabled
        existing.updated_at = datetime.utcnow()
        return NotifyChannelOut.model_validate(existing)
    ch = NotifyChannel(
        user_id=user.id,
        channel=payload.channel,
        target=payload.target,
        enabled=payload.enabled,
    )
    db.add(ch)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise Conflict("channel already bound", code="channel_conflict") from exc
    return NotifyChannelOut.model_validate(ch)


@router.post("/notify-channels/{channel}/test", response_model=MessageOut)
async def test_channel(
    channel: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    ch = await db.scalar(
        select(NotifyChannel).where(
            NotifyChannel.user_id == user.id, NotifyChannel.channel == channel
        )
    )
    if ch is None:
        raise NotFound("channel not bound", code="channel_not_found")
    db.add(
        NotificationLog(
            user_id=user.id, channel=channel, type="test",
            payload={"message": "Hello from CopyTrader 👋"},
            status="sent", sent_at=datetime.utcnow(),
        )
    )
    return MessageOut(message="test_sent", data={"channel": channel, "target": ch.target})


@router.get("/update", response_model=UpdateInfoOut)
async def update_info(_user: User = Depends(get_current_user)) -> UpdateInfoOut:
    return UpdateInfoOut(
        current_version=__version__,
        latest_version=__version__,
        has_update=False,
        release_notes=None,
    )


@router.post("/update/{account_id}", response_model=MessageOut)
async def trigger_account_update(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    acc = await db.get(ExchangeAccount, account_id)
    if acc is None or acc.user_id != user.id:
        raise NotFound("account not found", code="account_not_found")
    # Real impl pushes a control msg to execution_engine.
    return MessageOut(message="update_triggered", data={"account_id": account_id})
