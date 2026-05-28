"""Position-mapping algebra tests.

These are the most important tests in the codebase — they verify all
20+ knobs from the Galaxy report section 3.4 actually combine correctly.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from engine.events import SignalEvent
from engine.position_mapper import (
    AccountSnapshot,
    MapperConfig,
    OrderIntent,
    PositionMapper,
)


# ── helpers ─────────────────────────────────────────────────────────


def _cfg(**overrides) -> MapperConfig:
    base: dict = dict(
        id=1,
        user_id=1,
        exchange_account_id=1,
        trader_id=1,
        money_mode="fixed",
        money_param={"amount": "100"},
        multiplier=Decimal("1"),
        initial_strategy="none",
        direction_limit="both",
        open_trigger={"kind": "market"},
        add_trigger={"kind": "market"},
        symbol_blacklist=[],
        symbol_whitelist=[],
        leverage=10,
        reverse=False,
    )
    base.update(overrides)
    return MapperConfig(**base)


def _snap(bal="1000", total="1200", first=False) -> AccountSnapshot:
    return AccountSnapshot(
        available_balance=Decimal(bal),
        total_assets=Decimal(total),
        is_first_event=first,
    )


def _snapshot_event(symbol="BTC-USDT-SWAP", side="long", qty="1", entry="65000", pnl="0"):
    return SignalEvent(
        schema="signal.v1",
        event_id="evt-1",
        source="okx_public",
        trader_id="abc",
        ts=0,
        kind="position_snapshot",
        payload={
            "positions": [
                {
                    "symbol": symbol,
                    "side": side,
                    "qty": qty,
                    "entry_px": entry,
                    "unrealized_pnl": pnl,
                }
            ]
        },
    )


def _order_event(symbol="BTC-USDT-SWAP", side="long", action="open", qty="0.5", px="65000"):
    return SignalEvent(
        schema="signal.v1",
        event_id="ord-1",
        source="binance_lead",
        trader_id="abc",
        ts=0,
        kind="order_open" if action != "close" else "order_close",
        payload={
            "symbol": symbol,
            "side": side,
            "action": action,
            "qty_delta": qty,
            "px": px,
        },
    )


# ── money modes ─────────────────────────────────────────────────────


class TestMoneyMode:
    @staticmethod
    def _expected(notional: str, price: str = "65000") -> Decimal:
        from decimal import ROUND_DOWN

        return (Decimal(notional) / Decimal(price)).quantize(
            Decimal("0.00000001"), rounding=ROUND_DOWN
        )

    def test_fixed_amount(self):
        cfg = _cfg(money_mode="fixed", money_param={"amount": "200"})
        m = PositionMapper()
        intents = m.map_event(cfg, _order_event(), _snap())
        assert len(intents) == 1
        # 200 / 65000 = 0.00307692
        assert intents[0].qty == self._expected("200")

    def test_full_percent_of_balance(self):
        cfg = _cfg(money_mode="full", money_param={"percent": "50"})
        m = PositionMapper()
        intents = m.map_event(cfg, _order_event(), _snap(bal="1000"))
        # 1000 * 50% = 500 ; 500 / 65000
        assert intents[0].qty == self._expected("500")

    def test_compound_percent_of_total(self):
        cfg = _cfg(money_mode="compound", money_param={"percent": "10"})
        m = PositionMapper()
        intents = m.map_event(cfg, _order_event(), _snap(total="2000"))
        # 2000 * 10% = 200 ; 200/65000
        assert intents[0].qty == self._expected("200")

    def test_multiplier_scales_qty(self):
        cfg = _cfg(money_mode="fixed", money_param={"amount": "100"}, multiplier=Decimal("3"))
        m = PositionMapper()
        intents = m.map_event(cfg, _order_event(), _snap())
        # 100 * 3 / 65000
        assert intents[0].qty == self._expected("300")


# ── triggers (3 kinds) ──────────────────────────────────────────────


class TestTriggers:
    def test_market_open(self):
        cfg = _cfg(open_trigger={"kind": "market"})
        intents = PositionMapper().map_event(cfg, _order_event(), _snap())
        assert intents[0].kind == "market"
        assert intents[0].px is None

    def test_avg_limit_long_below_avg(self):
        """For LONG entries with avg_limit, we want to BUY below avg."""
        cfg = _cfg(open_trigger={"kind": "avg_limit", "edge_pct": "1"})
        ev = _order_event(side="long", px="65000")
        intents = PositionMapper().map_event(cfg, ev, _snap())
        assert intents[0].kind == "limit"
        # 65000 * (1 - 0.01) = 64350
        assert intents[0].px == Decimal("64350.00000000")

    def test_avg_limit_short_above_avg(self):
        cfg = _cfg(open_trigger={"kind": "avg_limit", "edge_pct": "1"})
        ev = _order_event(side="short", px="65000")
        intents = PositionMapper().map_event(cfg, ev, _snap())
        assert intents[0].kind == "limit"
        # 65000 * (1 + 0.01) = 65650
        assert intents[0].px == Decimal("65650.00000000")

    def test_add_limit_uses_add_price(self):
        """add_limit reference is THIS add's price, not avg."""
        cfg = _cfg(add_trigger={"kind": "add_limit", "edge_pct": "0.5"})
        ev = _order_event(side="long", action="increase", px="70000")
        intents = PositionMapper().map_event(cfg, ev, _snap())
        assert intents[0].kind == "limit"
        # 70000 * (1 - 0.005) = 69650
        assert intents[0].px == Decimal("69650.00000000")
        assert intents[0].action == "increase"


# ── initial_strategy ────────────────────────────────────────────────


class TestInitialStrategy:
    def test_none_skips_existing_positions(self):
        cfg = _cfg(initial_strategy="none")
        intents = PositionMapper().map_event(cfg, _snapshot_event(), _snap(first=True))
        assert intents == []

    def test_only_loss_skips_profit_positions(self):
        cfg = _cfg(initial_strategy="only_loss")
        ev = _snapshot_event(pnl="100")  # profit
        intents = PositionMapper().map_event(cfg, ev, _snap(first=True))
        assert intents == []

    def test_only_loss_copies_loss_positions(self):
        cfg = _cfg(initial_strategy="only_loss")
        ev = _snapshot_event(pnl="-50")  # loss
        intents = PositionMapper().map_event(cfg, ev, _snap(first=True))
        assert len(intents) == 1

    def test_all_copies_everything(self):
        cfg = _cfg(initial_strategy="all")
        ev = _snapshot_event(pnl="100")
        intents = PositionMapper().map_event(cfg, ev, _snap(first=True))
        assert len(intents) == 1

    def test_initial_strategy_doesnt_apply_after_first_event(self):
        cfg = _cfg(initial_strategy="none")
        # is_first_event=False — even with 'none' we should copy new opens
        intents = PositionMapper().map_event(cfg, _order_event(), _snap(first=False))
        assert len(intents) == 1


# ── direction_limit / reverse / blacklist ──────────────────────────


class TestFilters:
    def test_long_only_blocks_short(self):
        cfg = _cfg(direction_limit="long_only")
        intents = PositionMapper().map_event(cfg, _order_event(side="short"), _snap())
        assert intents == []

    def test_short_only_blocks_long(self):
        cfg = _cfg(direction_limit="short_only")
        intents = PositionMapper().map_event(cfg, _order_event(side="long"), _snap())
        assert intents == []

    def test_reverse_flips_side(self):
        cfg = _cfg(reverse=True)
        intents = PositionMapper().map_event(cfg, _order_event(side="long"), _snap())
        assert len(intents) == 1
        assert intents[0].side == "short"

    def test_blacklist_blocks_symbol(self):
        cfg = _cfg(symbol_blacklist=["BTC-USDT-SWAP"])
        intents = PositionMapper().map_event(cfg, _order_event(), _snap())
        assert intents == []

    def test_whitelist_only_allows_listed(self):
        cfg = _cfg(symbol_whitelist=["ETH-USDT-SWAP"])
        intents = PositionMapper().map_event(cfg, _order_event(symbol="BTC-USDT-SWAP"), _snap())
        assert intents == []
        intents = PositionMapper().map_event(cfg, _order_event(symbol="ETH-USDT-SWAP"), _snap())
        assert len(intents) == 1


# ── close ───────────────────────────────────────────────────────────


class TestCloseEvent:
    def test_close_with_local_position_creates_reduce_only(self):
        from engine.events import PositionItem

        cfg = _cfg()
        ev = _order_event(action="close")
        snap = _snap()
        snap.local_position = PositionItem(
            symbol="BTC-USDT-SWAP",
            side="long",
            qty=Decimal("0.5"),
            entry_px=Decimal("65000"),
        )
        intents = PositionMapper().map_event(cfg, ev, snap)
        assert len(intents) == 1
        assert intents[0].reduce_only is True
        assert intents[0].action == "close"
        assert intents[0].qty == Decimal("0.5")

    def test_close_without_local_position_is_noop(self):
        cfg = _cfg()
        ev = _order_event(action="close")
        intents = PositionMapper().map_event(cfg, ev, _snap())
        assert intents == []
