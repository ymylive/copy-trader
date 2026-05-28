"""Auth-related Pydantic models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.common import APIModel


class RegisterIn(APIModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    invite_code: Optional[str] = None


class LoginIn(APIModel):
    username: str
    password: str


class TokenOut(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(APIModel):
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    invite_code: Optional[str] = None
    referred_by: Optional[int] = None
    level: int
    referral_rate: float
    created_at: datetime


class PasswordChangeIn(APIModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)
