"""Referral / invite schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import APIModel


class InviteSummaryOut(APIModel):
    invite_code: str
    referral_rate: float
    total_invitees: int
    total_commission: float
    pending_commission: float


class ReferralRecordOut(APIModel):
    id: int
    invitee_id: int
    invitee_username: Optional[str] = None
    registered_at: datetime
    paid_amount: float
    commission: float
    status: str


class CommissionWithdrawIn(APIModel):
    amount: float = Field(gt=0)
    address: Optional[str] = None
