"""Risk guard tests."""
from __future__ import annotations

from decimal import Decimal

from engine.events import PositionItem
from engine.position_mapper import MapperConfig
from engine.risk import RiskAction, RiskGuard, RiskInputs


def _cfg() -> MapperConfig:
    return MapperConfig(
        id=1,
        user_id=1,
        exchange_account_id=1,
        trader_id=1,
        multiplier=Decimal("1"),
    )


def _pos(symbol="BTC-USDT-SWAP", side="long", qty="1", entry="65000"):
    return PositionItem(
        symbol=symbol,
        side=side,
        qty=Decimal(qty),
        entry_px=Decimal(entry),
    )


def test_ok_when_no_rules():
    ri = RiskInputs(
        cfg=_cfg(),
        local_positions=[_pos()],
        mark_prices={"BTC-USDT-SWAP": Decimal("65000")},
        account_nav=Decimal("1000"),
        baseline_nav=Decimal("1000"),
        tp={},
        sl={},
        loss_threshold={},
        safety_cushion={},
        refill={},
    )
    assert RiskGuard().evaluate(ri).action is RiskAction.OK


def test_loss_threshold_triggers_pause_and_close():
    # long 1 BTC @ 65000, mark 60000 → pnl = -5000
    ri = RiskInputs(
        cfg=_cfg(),
        local_positions=[_pos()],
        mark_prices={"BTC-USDT-SWAP": Decimal("60000")},
        account_nav=Decimal("1000"),
        baseline_nav=Decimal("1000"),
        tp={},
        sl={},
        loss_threshold={"usdt": "1000", "action": "pause_and_close"},
        safety_cushion={},
        refill={},
    )
    d = RiskGuard().evaluate(ri)
    assert d.action is RiskAction.PAUSE_AND_CLOSE
    assert d.intents and d.intents[0].reduce_only is True


def test_safety_cushion_decays_multiplier():
    ri = RiskInputs(
        cfg=_cfg(),
        local_positions=[],
        mark_prices={},
        account_nav=Decimal("700"),       # down 30%
        baseline_nav=Decimal("1000"),
        tp={},
        sl={},
        loss_threshold={},
        safety_cushion={"nav_drop_pct": "20", "decay_factor": "0.5"},
        refill={},
    )
    d = RiskGuard().evaluate(ri)
    assert d.action is RiskAction.DECAY_MULTIPLIER
    assert d.new_multiplier == Decimal("0.5000")


def test_take_profit_partial_close():
    ri = RiskInputs(
        cfg=_cfg(),
        local_positions=[_pos()],
        mark_prices={"BTC-USDT-SWAP": Decimal("71500")},  # +10%
        account_nav=Decimal("1000"),
        baseline_nav=Decimal("1000"),
        tp={"enabled": True, "trigger_pct": "10", "qty_pct": "50"},
        sl={},
        loss_threshold={},
        safety_cushion={},
        refill={},
    )
    d = RiskGuard().evaluate(ri)
    assert d.action is RiskAction.CLOSE_PARTIAL
    assert d.intents[0].qty == Decimal("0.50000000")


def test_stop_loss_full_close():
    ri = RiskInputs(
        cfg=_cfg(),
        local_positions=[_pos()],
        mark_prices={"BTC-USDT-SWAP": Decimal("58500")},  # -10%
        account_nav=Decimal("1000"),
        baseline_nav=Decimal("1000"),
        tp={},
        sl={"enabled": True, "trigger_pct": "10", "qty_pct": "100"},
        loss_threshold={},
        safety_cushion={},
        refill={},
    )
    d = RiskGuard().evaluate(ri)
    assert d.action is RiskAction.CLOSE_ALL


def test_refill_triggers_when_price_back_to_avg():
    ri = RiskInputs(
        cfg=_cfg(),
        local_positions=[_pos(entry="65000")],
        mark_prices={"BTC-USDT-SWAP": Decimal("65100")},  # within 0.3%
        account_nav=Decimal("1000"),
        baseline_nav=Decimal("1000"),
        tp={},
        sl={},
        loss_threshold={},
        safety_cushion={},
        refill={"refill_on_back_to_avg": True, "allow_re_tp": True},
        tp_triggered_symbols={"BTC-USDT-SWAP"},
    )
    d = RiskGuard().evaluate(ri)
    assert d.action is RiskAction.REFILL
