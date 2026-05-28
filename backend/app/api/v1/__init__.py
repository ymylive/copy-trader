"""V1 API router aggregation."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    auth,
    copy_configs,
    dashboard,
    invite,
    realtime,
    shop,
    system,
    traders,
    wallet,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(copy_configs.router, prefix="/copy-configs", tags=["copy-configs"])
api_router.include_router(traders.router, prefix="/traders", tags=["traders"])
api_router.include_router(shop.router, prefix="/shop", tags=["shop"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(invite.router, prefix="/invite", tags=["invite"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(realtime.router, tags=["realtime"])  # /ws/* + /internal/notify
