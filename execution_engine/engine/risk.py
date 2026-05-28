"""RiskGuard — TP/SL, loss_threshold, safety_cushion, refill, side filtering.

Stateless API: each method takes the relevant runtime state, returns a
:class:`RiskDecision`. The runner is responsible for actually applying
those decisions (sending close orders, decaying multiplier, pausing the
config in PG).

Galaxy report section 3.4 maps to the following fields:

    tp / sl ::
        {"enabled": bool,
         "cycle": bool,         # if True, allow re-trigger after refill
         "qty_pct": "50",       # % of accumulated position to close
         "trigger_pct": "10"}   # pnl% threshold

    loss_threshold ::
        {"usdt": "100", "action": "pause_and_close"}

    safety_cushion ::
        {"nav_drop_pct": "20", "decay_factor": "0.5"}

    refill ::
        {"refill_on_back_to_avg": True, "allow_re_tp": True}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from .events import PositionItem
from .metrics import risk_triggers
from .position_mapper import MapperConfig, OrderIntent, Side


class RiskAction(str, Enum):
    OK = "ok"                          # nothing to do
    CLOSE_PARTIAL = "close_partial"    # close ``qty_pct`` of the position
    CLOSE_ALL = "close_all"            # close everything for this symbol
    PAUSE_AND_CLOSE = "pause_and_close"  # close + pause whole config
    DECAY_MULTIPLIER = "decay_multiplier"  # safety cushion → reduce multiplier
    REFILL = "refill"                  # price has returned to avg → re-open


@dataclass(slots=True)
class RiskDecision:
    action: RiskAction
    reason: str = ""
    intents: list[OrderIntent] = field(default_factory=list)
    new_multiplier: Optional[Decimal] = None


@dataclass(slots=True)
class RiskInputs:
    """All the runtime facts the risk guard needs."""

    cfg: MapperConfig
    # all positions opened by this copy_config (could be many symbols)
    local_positions: list[PositionItem]
    # mark prices keyed by unified symbol
    mark_prices: dict[str, Decimal]
    # current account net asset value (USDT)
    account_nav: Decimal
    # historical baseline NAV used for safety_cushion (set at config start)
    baseline_nav: Decimal
    # raw JSONB from copy_configs
    tp: dict[str, Any]
    sl: dict[str, Any]
    loss_threshold: dict[str, Any]
    safety_cushion: dict[str, Any]
    refill: dict[str, Any]
    # bookkeeping for refill: last avg price + last tp event timestamps per symbol
    tp_triggered_symbols: set[str] = field(default_factory=set)


class RiskGuard:
    """Pure-Python, no IO. The runner glues this to the exchange."""

    # ─────────────────────────────────────────────────────────────────
    def evaluate(self, ri: RiskInputs) -> RiskDecision:
        """Run every rule in order; return the **first** non-OK decision."""
        # 1. loss_threshold (hard stop — takes precedence)
        d = self._check_loss_threshold(ri)
        if d.action is not RiskAction.OK:
            return d

        # 2. safety_cushion (decay multiplier)
        d = self._check_safety_cushion(ri)
        if d.action is not RiskAction.OK:
            return d

        # 3. take-profit / stop-loss per symbol
        d = self._check_tp_sl(ri)
        if d.action is not RiskAction.OK:
            return d

        # 4. refill (only if a TP previously fired)
        d = self._check_refill(ri)
        return d

    # ── helpers ─────────────────────────────────────────────────────
    def _total_pnl_usdt(self, ri: RiskInputs) -> Decimal:
        total = Decimal("0")
        for p in ri.local_positions:
            mp = ri.mark_prices.get(p.symbol)
            if mp is None or p.entry_px is None:
                continue
            # unrealized = (mp - entry) * qty * (long ? +1 : -1)
            direction = Decimal("1") if p.side == "long" else Decimal("-1")
            total += (mp - p.entry_px) * p.qty * direction
        return total

    def _close_intents(
        self,
        ri: RiskInputs,
        qty_pct: Decimal = Decimal("100"),
        reason: str = "",
    ) -> list[OrderIntent]:
        out: list[OrderIntent] = []
        ratio = qty_pct / Decimal("100")
        for p in ri.local_positions:
            close_qty = (p.qty * ratio).quantize(Decimal("0.00000001"))
            if close_qty <= 0:
                continue
            # to close a LONG we sell, to close a SHORT we buy — adapter handles it
            opposite: Side = "short" if p.side == "long" else "long"
            out.append(
                OrderIntent(
                    symbol=p.symbol,
                    side=opposite,                 # used by adapter to choose buy/sell
                    action="close" if qty_pct >= 100 else "reduce",
                    qty=close_qty,
                    kind="market",
                    reduce_only=True,
                    meta={"reason": reason},
                )
            )
        return out

    # ── rule implementations ────────────────────────────────────────
    def _check_loss_threshold(self, ri: RiskInputs) -> RiskDecision:
        usdt = ri.loss_threshold.get("usdt") if ri.loss_threshold else None
        if usdt is None:
            return RiskDecision(RiskAction.OK)
        try:
            threshold = Decimal(str(usdt))
        except Exception:  # noqa: BLE001
            return RiskDecision(RiskAction.OK)
        if threshold <= 0:
            return RiskDecision(RiskAction.OK)
        pnl = self._total_pnl_usdt(ri)
        if pnl <= -threshold:
            risk_triggers.labels(rule="loss_threshold").inc()
            return RiskDecision(
                action=RiskAction.PAUSE_AND_CLOSE,
                reason=f"loss_threshold hit: pnl={pnl} <= -{threshold}",
                intents=self._close_intents(ri, Decimal("100"), reason="loss_threshold"),
            )
        return RiskDecision(RiskAction.OK)

    def _check_safety_cushion(self, ri: RiskInputs) -> RiskDecision:
        if not ri.safety_cushion or ri.baseline_nav <= 0:
            return RiskDecision(RiskAction.OK)
        drop_pct_cfg = ri.safety_cushion.get("nav_drop_pct")
        if drop_pct_cfg is None:
            return RiskDecision(RiskAction.OK)
        try:
            drop_pct = Decimal(str(drop_pct_cfg))
            decay = Decimal(str(ri.safety_cushion.get("decay_factor", "0.5")))
        except Exception:  # noqa: BLE001
            return RiskDecision(RiskAction.OK)
        current_drop = (
            (ri.baseline_nav - ri.account_nav) / ri.baseline_nav * Decimal("100")
        )
        if current_drop >= drop_pct:
            risk_triggers.labels(rule="safety_cushion").inc()
            new_mult = (ri.cfg.multiplier * decay).quantize(Decimal("0.0001"))
            return RiskDecision(
                action=RiskAction.DECAY_MULTIPLIER,
                reason=f"safety_cushion: nav dropped {current_drop:.2f}% >= {drop_pct}%",
                new_multiplier=new_mult,
            )
        return RiskDecision(RiskAction.OK)

    def _check_tp_sl(self, ri: RiskInputs) -> RiskDecision:
        # per-symbol pnl%
        for p in ri.local_positions:
            mp = ri.mark_prices.get(p.symbol)
            if mp is None or p.entry_px is None or p.entry_px <= 0 or p.qty <= 0:
                continue
            direction = Decimal("1") if p.side == "long" else Decimal("-1")
            pnl_pct = (mp - p.entry_px) / p.entry_px * direction * Decimal("100")

            if ri.tp.get("enabled") and pnl_pct >= Decimal(str(ri.tp.get("trigger_pct", "999999"))):
                qty_pct = Decimal(str(ri.tp.get("qty_pct", "100")))
                risk_triggers.labels(rule="tp").inc()
                ri.tp_triggered_symbols.add(p.symbol)
                return RiskDecision(
                    action=(
                        RiskAction.CLOSE_PARTIAL if qty_pct < 100 else RiskAction.CLOSE_ALL
                    ),
                    reason=f"tp hit for {p.symbol}: {pnl_pct:.2f}%",
                    intents=self._close_intents(
                        RiskInputs(
                            cfg=ri.cfg,
                            local_positions=[p],
                            mark_prices=ri.mark_prices,
                            account_nav=ri.account_nav,
                            baseline_nav=ri.baseline_nav,
                            tp=ri.tp,
                            sl=ri.sl,
                            loss_threshold=ri.loss_threshold,
                            safety_cushion=ri.safety_cushion,
                            refill=ri.refill,
                        ),
                        qty_pct,
                        reason="tp",
                    ),
                )
            if ri.sl.get("enabled") and pnl_pct <= -Decimal(str(ri.sl.get("trigger_pct", "999999"))):
                qty_pct = Decimal(str(ri.sl.get("qty_pct", "100")))
                risk_triggers.labels(rule="sl").inc()
                return RiskDecision(
                    action=(
                        RiskAction.CLOSE_PARTIAL if qty_pct < 100 else RiskAction.CLOSE_ALL
                    ),
                    reason=f"sl hit for {p.symbol}: {pnl_pct:.2f}%",
                    intents=self._close_intents(
                        RiskInputs(
                            cfg=ri.cfg,
                            local_positions=[p],
                            mark_prices=ri.mark_prices,
                            account_nav=ri.account_nav,
                            baseline_nav=ri.baseline_nav,
                            tp=ri.tp,
                            sl=ri.sl,
                            loss_threshold=ri.loss_threshold,
                            safety_cushion=ri.safety_cushion,
                            refill=ri.refill,
                        ),
                        qty_pct,
                        reason="sl",
                    ),
                )
        return RiskDecision(RiskAction.OK)

    def _check_refill(self, ri: RiskInputs) -> RiskDecision:
        """If a TP fired earlier AND price has returned to entry avg → refill."""
        if not ri.refill or not ri.refill.get("refill_on_back_to_avg"):
            return RiskDecision(RiskAction.OK)
        if not ri.tp_triggered_symbols:
            return RiskDecision(RiskAction.OK)
        # The runner is expected to track the last-known avg price per symbol;
        # we emit a REFILL signal and let the runner reconstruct the qty.
        for sym in list(ri.tp_triggered_symbols):
            mp = ri.mark_prices.get(sym)
            avg = None
            for p in ri.local_positions:
                if p.symbol == sym:
                    avg = p.entry_px
                    break
            if mp is None or avg is None or avg <= 0:
                continue
            # within 0.3% of avg → trigger
            diff_pct = (mp - avg) / avg * Decimal("100")
            if abs(diff_pct) <= Decimal("0.3"):
                risk_triggers.labels(rule="refill").inc()
                return RiskDecision(
                    action=RiskAction.REFILL,
                    reason=f"refill {sym}: price back to avg within 0.3%",
                )
        return RiskDecision(RiskAction.OK)
