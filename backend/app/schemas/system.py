"""System / notification schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import APIModel


class NotifyChannelIn(APIModel):
    channel: str = Field(pattern=r"^(tg|email|wechat|sms)$")
    target: str = Field(min_length=1, max_length=256)
    enabled: bool = True


class NotifyChannelOut(APIModel):
    id: int
    channel: str
    target: str
    enabled: bool
    created_at: datetime


class UpdateInfoOut(APIModel):
    current_version: str
    latest_version: str
    has_update: bool
    release_notes: Optional[str] = None
