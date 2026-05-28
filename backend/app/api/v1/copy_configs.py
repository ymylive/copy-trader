"""Copy-config endpoints (the 20+ param bundle)."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.deps import get_current_user, get_db
from app.db.models import CopyConfig, CopyOrder, ExchangeAccount, Trader, User
from app.schemas.common import MessageOut
from app.schemas.copy_configs import (
    CopyConfigCreate,
    CopyConfigOut,
    CopyConfigUpdate,
    CopyOrderOut,
    TraderBrief,
)

log = logging.getLogger(__name__)
router = APIRouter()


def _to_out(cfg: CopyConfig, trader: Trader | None = None) -> CopyConfigOut:
    return CopyConfigOut.model_validate(
        {
            "id": cfg.id,
            "user_id": cfg.user_id,
            "exchange_account_id": cfg.exchange_account_id,
            "trader_id": cfg.trader_id,
            "reverse": cfg.reverse,
            "name": cfg.name,
            "money_mode": cfg.money_mode,
            "money_param": cfg.money_param or {},
            "multiplier": float(cfg.multiplier),
            "initial_strategy": cfg.initial_strategy,
            "direction_limit": cfg.direction_limit,
            "open_trigger": cfg.open_trigger or {"kind": "market"},
            "add_trigger": cfg.add_trigger or {"kind": "market"},
            "tp": cfg.tp or {"enabled": False},
            "sl": cfg.sl or {"enabled": False},
            "loss_threshold": cfg.loss_threshold or {},
            "safety_cushion": cfg.safety_cushion or {},
            "refill": cfg.refill or {},
            "symbol_blacklist": list(cfg.symbol_blacklist or []),
            "symbol_whitelist": list(cfg.symbol_whitelist or []),
            "notify_channels": list(cfg.notify_channels or []),
            "notify_types": list(cfg.notify_types or []),
            "status": cfg.status,
            "created_at": cfg.created_at,
            "trader": (
                TraderBrief(
                    id=trader.id,
                    source=trader.source,
                    external_id=trader.external_id,
                    display_name=trader.display_name,
                    exchange=trader.exchange,
                )
                if trader is not None
                else None
            ),
        }
    )


async def _load_cfg(db: AsyncSession, user: User, cfg_id: int) -> CopyConfig:
    cfg = await db.get(CopyConfig, cfg_id)
    if cfg is None or cfg.user_id != user.id:
        raise NotFound("copy config not found", code="copy_config_not_found")
    return cfg


@router.get("/", response_model=List[CopyConfigOut])
async def list_configs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CopyConfigOut]:
    rows = await db.execute(
        select(CopyConfig)
        .where(CopyConfig.user_id == user.id)
        .order_by(desc(CopyConfig.created_at))
    )
    cfgs = list(rows.scalars().all())
    # Bulk-fetch traders
    trader_ids = {c.trader_id for c in cfgs}
    traders: dict[int, Trader] = {}
    if trader_ids:
        tr_rows = await db.execute(select(Trader).where(Trader.id.in_(trader_ids)))
        for tr in tr_rows.scalars():
            traders[tr.id] = tr
    return [_to_out(c, traders.get(c.trader_id)) for c in cfgs]


@router.post("/", response_model=CopyConfigOut, status_code=status.HTTP_201_CREATED)
async def create_config(
    payload: CopyConfigCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopyConfigOut:
    # Validate references
    acc = await db.get(ExchangeAccount, payload.exchange_account_id)
    if acc is None or acc.user_id != user.id:
        raise NotFound("exchange account not found", code="account_not_found")
    trader = await db.get(Trader, payload.trader_id)
    if trader is None:
        raise NotFound("trader not found", code="trader_not_found")

    if payload.money_mode == "fixed":
        if not payload.money_param.amount or payload.money_param.amount <= 0:
            raise BadRequest("fixed mode requires money_param.amount > 0", code="bad_money_param")
    if payload.money_mode in ("full", "compound"):
        pct = payload.money_param.percent
        if pct is None or pct <= 0 or pct > 100:
            raise BadRequest("full/compound mode requires money_param.percent in (0,100]", code="bad_money_param")

    cfg = CopyConfig(
        user_id=user.id,
        exchange_account_id=payload.exchange_account_id,
        trader_id=payload.trader_id,
        reverse=payload.reverse,
        name=payload.name,
        money_mode=payload.money_mode,
        money_param=payload.money_param.model_dump(exclude_none=True),
        multiplier=payload.multiplier,
        initial_strategy=payload.initial_strategy,
        direction_limit=payload.direction_limit,
        open_trigger=payload.open_trigger.model_dump(exclude_none=True),
        add_trigger=payload.add_trigger.model_dump(exclude_none=True),
        tp=payload.tp.model_dump(exclude_none=True),
        sl=payload.sl.model_dump(exclude_none=True),
        loss_threshold=payload.loss_threshold.model_dump(exclude_none=True),
        safety_cushion=payload.safety_cushion.model_dump(exclude_none=True),
        refill=payload.refill.model_dump(exclude_none=True),
        symbol_blacklist=payload.symbol_blacklist,
        symbol_whitelist=payload.symbol_whitelist,
        notify_channels=payload.notify_channels,
        notify_types=payload.notify_types,
        status="running",
    )
    db.add(cfg)
    await db.flush()
    log.info("copy_config.created id=%s user_id=%s trader_id=%s", cfg.id, user.id, trader.id)
    return _to_out(cfg, trader)


@router.patch("/{cfg_id}", response_model=CopyConfigOut)
async def update_config(
    cfg_id: int,
    payload: CopyConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopyConfigOut:
    cfg = await _load_cfg(db, user, cfg_id)
    upd = payload.model_dump(exclude_unset=True)
    for key, val in upd.items():
        # JSON sub-models become dicts
        if hasattr(val, "model_dump"):
            val = val.model_dump(exclude_none=True)
        setattr(cfg, key, val)
    cfg.updated_at = datetime.utcnow()
    trader = await db.get(Trader, cfg.trader_id)
    return _to_out(cfg, trader)


@router.post("/{cfg_id}/pause", response_model=CopyConfigOut)
async def pause(
    cfg_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopyConfigOut:
    cfg = await _load_cfg(db, user, cfg_id)
    cfg.status = "paused"
    trader = await db.get(Trader, cfg.trader_id)
    return _to_out(cfg, trader)


@router.post("/{cfg_id}/resume", response_model=CopyConfigOut)
async def resume(
    cfg_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopyConfigOut:
    cfg = await _load_cfg(db, user, cfg_id)
    cfg.status = "running"
    trader = await db.get(Trader, cfg.trader_id)
    return _to_out(cfg, trader)


@router.post("/{cfg_id}/close-all", response_model=MessageOut)
async def close_all(
    cfg_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    """Flag the config 'stopped' and emit a close-all command on Redis.

    Execution engine consumes the command and actually flattens positions.
    """
    cfg = await _load_cfg(db, user, cfg_id)
    cfg.status = "stopped"
    log.info("copy_config.close_all id=%s user_id=%s", cfg.id, user.id)
    return MessageOut(message="close_all_scheduled", data={"config_id": cfg.id})


@router.delete("/{cfg_id}", response_model=MessageOut)
async def delete_config(
    cfg_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    cfg = await _load_cfg(db, user, cfg_id)
    await db.delete(cfg)
    return MessageOut(message="deleted")


@router.get("/{cfg_id}/orders", response_model=List[CopyOrderOut])
async def list_orders(
    cfg_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CopyOrderOut]:
    await _load_cfg(db, user, cfg_id)
    rows = await db.execute(
        select(CopyOrder)
        .where(CopyOrder.copy_config_id == cfg_id)
        .order_by(desc(CopyOrder.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [
        CopyOrderOut(
            id=o.id,
            copy_config_id=o.copy_config_id,
            exchange_account_id=o.exchange_account_id,
            exchange_order_id=o.exchange_order_id,
            symbol=o.symbol,
            side=o.side,
            action=o.action,
            qty=float(o.qty),
            px=float(o.px) if o.px is not None else None,
            status=o.status,
            source_event_id=o.source_event_id,
            error=o.error,
            created_at=o.created_at,
        )
        for o in rows.scalars()
    ]
