"""Seed demo data — 8 listed traders + 1 demo user.

Usage:
    cd backend
    DATABASE_URL=sqlite+aiosqlite:///./demo.db python -m infra.scripts.seed_demo_data
    # or with Postgres:
    DATABASE_URL=postgresql+asyncpg://copytrader:copytrader@localhost/copytrader python ...
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.db.base import async_session_maker, engine, Base  # noqa: E402
from app.db.models import (  # noqa: E402
    User, ExchangeAccount, Trader, WalletBalance, WalletTransaction,
    SubscriptionResource, CopyConfig,
)
from app.core.security import hash_password  # noqa: E402


TRADERS = [
    # (source, external_id, display_name, exchange, stats)
    (
        "bicoin", "79346", "茂茂大魔王", "okx",
        {"total_pnl": "1343829.94", "return_pct": "14539.61", "size_usdt": "7618.91",
         "sharpe": None, "win_rate": "0.3440", "max_drawdown": "0.0257",
         "active_days": 2209, "is_lead": True, "is_hidden": False},
    ),
    (
        "bicoin", "369319", "风火山林Trader", "binance",
        {"total_pnl": "1927532.79", "return_pct": "6880.06", "size_usdt": "89999.16",
         "sharpe": None, "win_rate": "0.4545", "max_drawdown": "0.0686",
         "active_days": 1705, "is_lead": True, "is_hidden": False},
    ),
    (
        "bicoin", "1030294", "牛的青山在", "okx",
        {"total_pnl": "297089.72", "return_pct": "10326.49", "size_usdt": "13292.43",
         "sharpe": None, "win_rate": "0.7500", "max_drawdown": "0.0115",
         "active_days": 899, "is_lead": True, "is_hidden": False},
    ),
    (
        "bicoin", "951891", "寒星日照", "okx",
        {"total_pnl": "408565.96", "return_pct": "343.37", "size_usdt": "138001.32",
         "sharpe": None, "win_rate": "0.4333", "max_drawdown": "0.1451",
         "active_days": 1218, "is_lead": True, "is_hidden": False},
    ),
    (
        "binance_lead", "4120066087544364033", "MaximizeSR", "binance",
        {"total_pnl_90d": "-319.96", "return_pct_90d": "-6.03", "size_usdt": "46358.66",
         "sharpe": "0.06", "win_rate_90d": "0.5129", "max_drawdown_90d": "0.0915",
         "active_days": 653, "is_lead": True, "is_hidden": True},
    ),
    (
        "binance_lead", "3904393221729556225", "Melanya", "binance",
        {"total_pnl_90d": "0.00", "return_pct_90d": "0.00", "size_usdt": "10177.62",
         "sharpe": "-0.13", "win_rate_90d": "0.0000", "max_drawdown_90d": "0.0000",
         "active_days": 802, "is_lead": True, "is_hidden": True},
    ),
    (
        "binance_lead", "3779422221599733504", "KNOTMAIN", "binance",
        {"total_pnl_90d": "365404.77", "return_pct_90d": "53.51", "size_usdt": None,
         "sharpe": "3.20", "win_rate_90d": "0.5783", "max_drawdown_90d": "0.1332",
         "active_days": None, "is_lead": True, "is_hidden": True, "data_stale": True},
    ),
    (
        "binance_lead", "4030560779244867073", "穩定暴擊 Crit", "binance",
        {"total_pnl_90d": "-102513.70", "return_pct_90d": "-57.91", "size_usdt": "69091.23",
         "sharpe": "-0.05", "win_rate_90d": "0.3276", "max_drawdown_90d": "0.6991",
         "active_days": 715, "is_lead": True, "is_hidden": True},
    ),
    # Hyperliquid example whale
    (
        "hyperliquid", "0x31ca8395cf837de08b24da3f660e77761dfb974b", "HL Whale α", "hyperliquid",
        {"total_pnl": "892341.50", "return_pct": "2150.0", "size_usdt": "1200000",
         "sharpe": "2.84", "win_rate": "0.6420", "max_drawdown": "0.0921",
         "active_days": 480, "is_lead": False, "is_hidden": False, "chain": "hyperliquid"},
    ),
    # EVM smart money example
    (
        "evm_smart_money", "0xa6c50d0b1a18a3b35eee85e4b9d3e4caa3a09e0c", "Smart $ — GMX prime", "gmx",
        {"total_pnl": "541200.00", "return_pct": "189.0", "size_usdt": "780000",
         "sharpe": "1.65", "win_rate": "0.5882", "max_drawdown": "0.1820",
         "active_days": 210, "is_lead": False, "is_hidden": False, "chain": "arbitrum"},
    ),
]


async def main() -> None:
    # Ensure tables exist (idempotent in SQLite; in Postgres run Alembic first)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as s:
        # demo user
        from sqlalchemy import select
        existing = (await s.execute(select(User).where(User.username == "demo"))).scalar_one_or_none()
        if existing is None:
            demo = User(
                username="demo",
                password_hash=hash_password("demo123"),
                email="demo@copytrader.local",
                invite_code="DEMO01",
                level=1,
                referral_rate=Decimal("0.10"),
            )
            s.add(demo)
            await s.flush()
            print(f"created demo user id={demo.id}")
        else:
            demo = existing
            print(f"demo user already exists id={demo.id}")

        # wallet balance
        bal = (await s.execute(select(WalletBalance).where(WalletBalance.user_id == demo.id))).scalar_one_or_none()
        if bal is None:
            s.add(WalletBalance(user_id=demo.id, currency="USDT", amount=Decimal("500.00")))

        # exchange accounts (账户1-4)
        accounts_data = [
            ("账户1", "binance", "12345678", "active"),
            ("账户2", "okx", "87654321", "active"),
            ("账户3", "gate", "52494073", "inactive"),
            ("账户4", "bitget", "99887766", "active"),
        ]
        for alias, exch, uid, status in accounts_data:
            exists = (await s.execute(
                select(ExchangeAccount).where(
                    ExchangeAccount.user_id == demo.id,
                    ExchangeAccount.alias == alias,
                )
            )).scalar_one_or_none()
            if exists is None:
                s.add(ExchangeAccount(
                    user_id=demo.id, alias=alias, tier="standard",
                    exchange=exch, uid=uid, status=status,
                    leverage_default=10,
                    egress_ips=["8.211.140.223", "43.153.149.108",
                                "101.36.104.169", "47.245.8.141"],
                    activated_at=datetime.now(timezone.utc) if status == "active" else None,
                    service_expires_at=datetime.now(timezone.utc) + timedelta(days=220),
                ))

        # subscription resources
        sku_data = [
            ("follow_slot", 9999),  # 永久 → year 9999
            ("follow_slot", 9999),
            ("follow_slot", 9999),
            ("order_slot", 220),    # 账户4 下单名额 220 天后到期
        ]
        cnt = (await s.execute(
            select(func_count(SubscriptionResource.id)).where(SubscriptionResource.user_id == demo.id)
            if False else select(SubscriptionResource).where(SubscriptionResource.user_id == demo.id)
        )).all()
        if not cnt:
            for sku, days in sku_data:
                s.add(SubscriptionResource(
                    user_id=demo.id, sku=sku,
                    purchase_time=datetime.now(timezone.utc),
                    expires_at=(datetime(9999, 12, 31, tzinfo=timezone.utc) if days == 9999
                                else datetime.now(timezone.utc) + timedelta(days=days)),
                    paid_amount=Decimal("80.00") if sku == "order_slot" else Decimal("35.00"),
                ))

        # traders
        for source, ext_id, name, exch, stats in TRADERS:
            existing = (await s.execute(
                select(Trader).where(Trader.source == source, Trader.external_id == ext_id)
            )).scalar_one_or_none()
            if existing is None:
                s.add(Trader(
                    source=source, external_id=ext_id, display_name=name,
                    exchange=exch, stats=stats, listed=True,
                    last_active_at=datetime.now(timezone.utc),
                    meta={"data_source": source.replace("_", " ").title()},
                ))

        await s.commit()
        print(f"seeded {len(TRADERS)} traders, 4 accounts, 4 subscriptions, wallet $500")


def func_count(x):
    from sqlalchemy import func
    return func.count(x)


if __name__ == "__main__":
    asyncio.run(main())
