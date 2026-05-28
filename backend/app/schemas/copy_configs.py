"""Copy-trade configuration schemas (the 20+ param bundle)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import APIModel


# JSON sub-payload helpers ─────────────────────────────────────────────


class TriggerCfg(APIModel):
    kind: str = Field(default="market", pattern=r"^(market|avg_limit|add_limit)$")
    edge_pct: Optional[float] = Field(default=None, ge=0, le=50)


class TpSlCfg(APIModel):
    enabled: bool = False
    cycle: Optional[bool] = None
    qty_pct: Optional[float] = Field(default=None, ge=0, le=100)
    trigger_pct: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None


class LossThresholdCfg(APIModel):
    usdt: Optional[float] = None
    action: Optional[str] = None  # pause_and_close


class SafetyCushionCfg(APIModel):
    nav_drop: Optional[float] = None
    decay_factor: Optional[float] = None


class RefillCfg(APIModel):
    refill_on_back_to_avg: Optional[bool] = None
    allow_re_tp: Optional[bool] = None


class MoneyParamCfg(APIModel):
    amount: Optional[float] = None
    percent: Optional[float] = None


# Main copy-config schemas ─────────────────────────────────────────────


class CopyConfigBase(APIModel):
    exchange_account_id: int
    trader_id: int
    reverse: bool = False
    name: str = Field(default="配置1", min_length=1, max_length=64)
    money_mode: str = Field(default="fixed", pattern=r"^(fixed|full|compound)$")
    money_param: MoneyParamCfg = Field(default_factory=MoneyParamCfg)
    multiplier: float = Field(default=1.0, gt=0, le=1000)
    initial_strategy: str = Field(default="none", pattern=r"^(none|only_loss|all)$")
    direction_limit: str = Field(default="both", pattern=r"^(both|long_only|short_only)$")
    open_trigger: TriggerCfg = Field(default_factory=TriggerCfg)
    add_trigger: TriggerCfg = Field(default_factory=TriggerCfg)
    tp: TpSlCfg = Field(default_factory=TpSlCfg)
    sl: TpSlCfg = Field(default_factory=TpSlCfg)
    loss_threshold: LossThresholdCfg = Field(default_factory=LossThresholdCfg)
    safety_cushion: SafetyCushionCfg = Field(default_factory=SafetyCushionCfg)
    refill: RefillCfg = Field(default_factory=RefillCfg)
    symbol_blacklist: List[str] = Field(default_factory=list)
    symbol_whitelist: List[str] = Field(default_factory=list)
    notify_channels: List[str] = Field(default_factory=list)
    notify_types: List[str] = Field(default_factory=list)


class CopyConfigCreate(CopyConfigBase):
    pass


class CopyConfigUpdate(APIModel):
    name: Optional[str] = None
    reverse: Optional[bool] = None
    money_mode: Optional[str] = None
    money_param: Optional[MoneyParamCfg] = None
    multiplier: Optional[float] = None
    initial_strategy: Optional[str] = None
    direction_limit: Optional[str] = None
    open_trigger: Optional[TriggerCfg] = None
    add_trigger: Optional[TriggerCfg] = None
    tp: Optional[TpSlCfg] = None
    sl: Optional[TpSlCfg] = None
    loss_threshold: Optional[LossThresholdCfg] = None
    safety_cushion: Optional[SafetyCushionCfg] = None
    refill: Optional[RefillCfg] = None
    symbol_blacklist: Optional[List[str]] = None
    symbol_whitelist: Optional[List[str]] = None
    notify_channels: Optional[List[str]] = None
    notify_types: Optional[List[str]] = None


class TraderBrief(APIModel):
    id: int
    source: str
    external_id: str
    display_name: Optional[str] = None
    exchange: Optional[str] = None


class CopyConfigOut(CopyConfigBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    trader: Optional[TraderBrief] = None


class CopyOrderOut(APIModel):
    id: int
    copy_config_id: int
    exchange_account_id: int
    exchange_order_id: Optional[str] = None
    symbol: str
    side: str
    action: str
    qty: float
    px: Optional[float] = None
    status: str
    source_event_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
