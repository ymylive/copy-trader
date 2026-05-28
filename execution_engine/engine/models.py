"""SQLAlchemy 2.0 ORM models — mirror of the backend tables.

We re-declare them inside the engine to avoid importing the backend package.
The schema matches ``infra/migrations/0001_init.sql``.
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
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
    types,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ── cross-DB type helpers (PG JSONB vs SQLite JSON, PG text[] vs SQLite JSON) ──
class JSONB(types.TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


class StringArray(types.TypeDecorator):
    impl = types.JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY
            return dialect.type_descriptor(ARRAY(types.Text()))
        return dialect.type_descriptor(types.JSON())

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return [] if dialect.name == "postgresql" else json.dumps([])
        if dialect.name == "postgresql":
            return list(value)
        return json.dumps(list(value))

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return []
        if dialect.name == "postgresql":
            return list(value)
        if isinstance(value, str):
            try:
                return list(json.loads(value))
            except Exception:  # noqa: BLE001
                return []
        return list(value)


# ───────────────────────────────────────────────────────────────────────
class ExchangeAccount(Base):
    __tablename__ = "exchange_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    alias: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(Text, nullable=False, default="standard")
    exchange: Mapped[str] = mapped_column(Text, nullable=False)
    uid: Mapped[str | None] = mapped_column(Text)
    api_key_enc: Mapped[str | None] = mapped_column(Text)
    api_secret_enc: Mapped[str | None] = mapped_column(Text)
    passphrase_enc: Mapped[str | None] = mapped_column(Text)
    leverage_default: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="inactive")
    egress_ips: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("user_id", "alias", name="uq_exch_acct_user_alias"),)


class Trader(Base):
    __tablename__ = "traders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    exchange: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    listed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_trader_src_ext"),)


class CopyConfig(Base):
    __tablename__ = "copy_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exchange_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False
    )
    trader_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("traders.id", ondelete="RESTRICT"), nullable=False
    )
    reverse: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str] = mapped_column(Text, nullable=False, default="配置1")
    money_mode: Mapped[str] = mapped_column(Text, nullable=False, default="fixed")
    money_param: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("1"))
    initial_strategy: Mapped[str] = mapped_column(Text, nullable=False, default="none")
    direction_limit: Mapped[str] = mapped_column(Text, nullable=False, default="both")
    open_trigger: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    add_trigger: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    tp: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    sl: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    loss_threshold: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    safety_cushion: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    refill: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    symbol_blacklist: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    symbol_whitelist: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    notify_channels: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    notify_types: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CopyOrder(Base):
    __tablename__ = "copy_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    copy_config_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("copy_configs.id", ondelete="CASCADE"), nullable=False
    )
    exchange_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exchange_accounts.id"), nullable=False
    )
    exchange_order_id: Mapped[str | None] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    px: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    source_event_id: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "copy_config_id", "source_event_id", name="uq_copy_orders_config_event"
        ),
    )


class PositionSnapshot(Base):
    __tablename__ = "positions_snapshots"

    # composite PK: (ts, exchange_account_id, symbol, side)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    exchange_account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    side: Mapped[str] = mapped_column(Text, primary_key=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    entry_px: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    lev: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    margin: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))


class NavCurve(Base):
    __tablename__ = "nav_curve"

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    exchange_account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    total_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )


class SubscriptionResource(Base):
    __tablename__ = "subscription_resources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    bound_account_id: Mapped[int | None] = mapped_column(BigInteger)
    purchase_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    coupon_id: Mapped[int | None] = mapped_column(BigInteger)
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("0")
    )
