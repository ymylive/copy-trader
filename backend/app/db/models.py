"""SQLAlchemy ORM models matching infra/migrations/0001_init.sql."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONB, StringArray


# ─── helpers ───────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.utcnow()


# BigIntPK PK that becomes plain INTEGER on SQLite (so AUTOINCREMENT works).
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")
BigIntFK = BigInteger().with_variant(Integer(), "sqlite")


# ─── users ─────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    invite_code: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    referred_by: Mapped[Optional[int]] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="SET NULL")
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    referral_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0.10")
    )
    totp_secret: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


# ─── exchange_accounts ────────────────────────────────────────────────


class ExchangeAccount(Base):
    __tablename__ = "exchange_accounts"
    __table_args__ = (UniqueConstraint("user_id", "alias", name="uq_exchange_accounts_user_alias"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(Text, nullable=False, default="standard")
    exchange: Mapped[str] = mapped_column(Text, nullable=False)
    uid: Mapped[Optional[str]] = mapped_column(Text)
    api_key_enc: Mapped[Optional[str]] = mapped_column(Text)
    api_secret_enc: Mapped[Optional[str]] = mapped_column(Text)
    passphrase_enc: Mapped[Optional[str]] = mapped_column(Text)
    leverage_default: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="inactive")
    egress_ips: Mapped[list[str]] = mapped_column(StringArray(), nullable=False, default=list)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    service_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


# ─── subscription_resources ───────────────────────────────────────────


class SubscriptionResource(Base):
    __tablename__ = "subscription_resources"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    bound_account_id: Mapped[Optional[int]] = mapped_column(
        BigIntPK, ForeignKey("exchange_accounts.id", ondelete="SET NULL")
    )
    purchase_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    coupon_id: Mapped[Optional[int]] = mapped_column(BigIntPK)
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )


# ─── wallet ───────────────────────────────────────────────────────────


class WalletBalance(Base):
    __tablename__ = "wallet_balances"

    user_id: Mapped[int] = mapped_column(
        BigIntPK,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(Text, primary_key=True, default="USDT")
    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="USDT")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    ref_sku: Mapped[Optional[str]] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )


# ─── traders ──────────────────────────────────────────────────────────


class Trader(Base):
    __tablename__ = "traders"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_traders_source_external"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(Text)
    exchange: Mapped[Optional[str]] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    listed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


# ─── copy_configs ─────────────────────────────────────────────────────


class CopyConfig(Base):
    __tablename__ = "copy_configs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exchange_account_id: Mapped[int] = mapped_column(
        BigIntPK,
        ForeignKey("exchange_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    trader_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("traders.id", ondelete="RESTRICT"), nullable=False
    )
    reverse: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str] = mapped_column(Text, nullable=False, default="配置1")
    money_mode: Mapped[str] = mapped_column(Text, nullable=False, default="fixed")
    money_param: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    multiplier: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, default=Decimal("1")
    )
    initial_strategy: Mapped[str] = mapped_column(Text, nullable=False, default="none")
    direction_limit: Mapped[str] = mapped_column(Text, nullable=False, default="both")
    open_trigger: Mapped[dict[str, Any]] = mapped_column(
        JSONB(), nullable=False, default=lambda: {"kind": "market"}
    )
    add_trigger: Mapped[dict[str, Any]] = mapped_column(
        JSONB(), nullable=False, default=lambda: {"kind": "market"}
    )
    tp: Mapped[dict[str, Any]] = mapped_column(
        JSONB(), nullable=False, default=lambda: {"enabled": False}
    )
    sl: Mapped[dict[str, Any]] = mapped_column(
        JSONB(), nullable=False, default=lambda: {"enabled": False}
    )
    loss_threshold: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    safety_cushion: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    refill: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    symbol_blacklist: Mapped[list[str]] = mapped_column(StringArray(), nullable=False, default=list)
    symbol_whitelist: Mapped[list[str]] = mapped_column(StringArray(), nullable=False, default=list)
    notify_channels: Mapped[list[str]] = mapped_column(StringArray(), nullable=False, default=list)
    notify_types: Mapped[list[str]] = mapped_column(StringArray(), nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


# ─── copy_orders ──────────────────────────────────────────────────────


class CopyOrder(Base):
    __tablename__ = "copy_orders"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    copy_config_id: Mapped[int] = mapped_column(
        BigIntPK,
        ForeignKey("copy_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    exchange_account_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("exchange_accounts.id"), nullable=False
    )
    exchange_order_id: Mapped[Optional[str]] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    px: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    source_event_id: Mapped[Optional[str]] = mapped_column(Text)
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


# ─── positions_snapshots (hypertable in PG; plain table in tests) ─────


class PositionSnapshot(Base):
    __tablename__ = "positions_snapshots"

    # composite PK ensures hypertable compatibility (ts must be in PK on TS).
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    exchange_account_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    entry_px: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    lev: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))


# ─── nav_curve ────────────────────────────────────────────────────────


class NavPoint(Base):
    __tablename__ = "nav_curve"

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    exchange_account_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    total_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )


# ─── notifications_log ────────────────────────────────────────────────


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )


class NotifyChannel(Base):
    """User-configured notification channels (TG/email/wechat/sms)."""

    __tablename__ = "notify_channels"
    __table_args__ = (UniqueConstraint("user_id", "channel", name="uq_notify_user_channel"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


# ─── login_history ────────────────────────────────────────────────────


class LoginHistory(Base):
    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ip: Mapped[Optional[str]] = mapped_column(Text)  # INET in PG; Text in tests
    geo: Mapped[Optional[str]] = mapped_column(Text)
    ua: Mapped[Optional[str]] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )


# ─── referral_records ─────────────────────────────────────────────────


class ReferralRecord(Base):
    __tablename__ = "referral_records"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    invitee_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )
    commission: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")


# ─── coupons ──────────────────────────────────────────────────────────


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE")
    )
    code: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    discount: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    sku_scope: Mapped[list[str]] = mapped_column(StringArray(), nullable=False, default=list)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )


# ─── traders watchlist (user-specific) ────────────────────────────────


class TraderWatchlist(Base):
    """Per-user trader watch / pin list."""

    __tablename__ = "trader_watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "trader_id", name="uq_trader_watch_user_trader"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    trader_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("traders.id", ondelete="CASCADE"), nullable=False
    )
    cookie_enc: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
