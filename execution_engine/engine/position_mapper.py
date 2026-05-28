"""PositionMapper — translate a SignalEvent into one or more OrderIntents.

This module is **pure**: it does no IO, only math. Inputs are:

* ``CopyConfig`` row (validated through :class:`MapperConfig`)
* :class:`SignalEvent`
* Live market snapshot: account balance, total assets, current local position, mark price.

It returns a list of :class:`OrderIntent` (the adapter layer handles execution).

Implements the full Galaxy report section 3.4 spec:
    - money_mode: fixed / full / compound
    - multiplier
    - initial_strategy: none / only_loss / all  (applied on first snapshot only)
    - direction_limit: both / long_only / short_only
    - open_trigger / add_trigger: market / avg_limit / add_limit + edge_pct
    - reverse-copy
    - symbol black/white-list

Risk rules (TP/SL/loss_threshold/safety_cushion/refill) live in ``risk.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from typing import Any, Iterable, Literal, Optional

from .events import PositionItem, SignalEvent

# ───────────────────────────────────────────────────────────────────────
# Data classes

Side = Literal["long", "short"]
Action = Literal["open", "increase", "reduce", "close"]
OrderKind = Literal["market", "limit"]


@dataclass(slots=True, frozen=True)
class OrderIntent:
    """Concrete instruction handed to an ExchangeAdapter.

    All numeric fields use Decimal; no floats anywhere.
    """

    symbol: str                      # unified BTC-USDT-SWAP
    side: Side                       # long/short  → translated to buy/sell by adapter
    action: Action
    qty: Decimal                     # always positive
    kind: OrderKind = "market"
    px: Optional[Decimal] = None     # required when kind=='limit'
    reduce_only: bool = False
    # extra context propagated to copy_orders for traceability
    source_event_id: Optional[str] = None
    leverage: Optional[int] = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MapperConfig:
    """A subset of CopyConfig flattened for use by the mapper.

    Use :meth:`from_orm` to build it from a SQLAlchemy ``CopyConfig`` row, or
    construct directly in tests.
    """

    id: int
    user_id: int
    exchange_account_id: int
    trader_id: int

    reverse: bool = False
    money_mode: str = "fixed"               # fixed/full/compound
    money_param: dict[str, Any] = field(default_factory=dict)
    multiplier: Decimal = Decimal("1")
    initial_strategy: str = "none"          # none/only_loss/all
    direction_limit: str = "both"           # both/long_only/short_only
    open_trigger: dict[str, Any] = field(default_factory=lambda: {"kind": "market"})
    add_trigger: dict[str, Any] = field(default_factory=lambda: {"kind": "market"})
    symbol_blacklist: list[str] = field(default_factory=list)
    symbol_whitelist: list[str] = field(default_factory=list)
    leverage: int = 10

    @classmethod
    def from_orm(cls, row: Any) -> "MapperConfig":
        return cls(
            id=row.id,
            user_id=row.user_id,
            exchange_account_id=row.exchange_account_id,
            trader_id=row.trader_id,
            reverse=row.reverse,
            money_mode=row.money_mode,
            money_param=dict(row.money_param or {}),
            multiplier=Decimal(str(row.multiplier or 1)),
            initial_strategy=row.initial_strategy,
            direction_limit=row.direction_limit,
            open_trigger=dict(row.open_trigger or {"kind": "market"}),
            add_trigger=dict(row.add_trigger or {"kind": "market"}),
            symbol_blacklist=list(row.symbol_blacklist or []),
            symbol_whitelist=list(row.symbol_whitelist or []),
            leverage=10,  # filled in by the runner via exchange_account.leverage_default
        )


@dataclass(slots=True)
class AccountSnapshot:
    """What the FollowerRunner has just queried about the user's local account."""

    available_balance: Decimal           # free USDT margin
    total_assets: Decimal                # total = balance + sum(unrealized_pnl)
    # current local position for the symbol; None if flat
    local_position: Optional[PositionItem] = None
    mark_price: Optional[Decimal] = None
    is_first_event: bool = False         # True only for the very first event we see


# ───────────────────────────────────────────────────────────────────────
# The mapper

class PositionMapper:
    """Stateless mapper; one instance per process is fine."""

    # ───── public entry point ─────
    def map_event(
        self,
        cfg: MapperConfig,
        event: SignalEvent,
        snap: AccountSnapshot,
    ) -> list[OrderIntent]:
        """Return zero or more intents implied by ``event``."""
        if event.kind == "position_snapshot":
            return self._map_snapshot(cfg, event, snap)
        if event.kind in ("order_open", "order_close"):
            return self._map_order(cfg, event, snap)
        # order_modify / margin_change → ignore for now (could trigger refills)
        return []

    # ───── snapshot path (initial_strategy controls behaviour) ─────
    def _map_snapshot(
        self,
        cfg: MapperConfig,
        event: SignalEvent,
        snap: AccountSnapshot,
    ) -> list[OrderIntent]:
        intents: list[OrderIntent] = []
        items: Iterable[PositionItem] = event.positions()

        for it in items:
            # filter by symbol black/white list, direction limit
            if not self._symbol_allowed(cfg, it.symbol):
                continue
            mapped_side = self._mapped_side(cfg, it.side)
            if mapped_side is None:
                continue

            # initial_strategy: only meaningful on FIRST event we ever see
            if snap.is_first_event:
                if cfg.initial_strategy == "none":
                    continue
                if cfg.initial_strategy == "only_loss":
                    pnl = it.unrealized_pnl or Decimal("0")
                    if pnl >= 0:
                        continue
                # 'all' → fall through

            target_qty = self._target_qty(cfg, it, snap)
            if target_qty <= 0:
                continue
            kind, px = self._open_order_kind(cfg, it)
            intents.append(
                OrderIntent(
                    symbol=it.symbol,
                    side=mapped_side,
                    action="open",
                    qty=target_qty,
                    kind=kind,
                    px=px,
                    reduce_only=False,
                    source_event_id=f"{event.event_id}:{it.symbol}:{it.side}",
                    leverage=cfg.leverage,
                )
            )
        return intents

    # ───── incremental order path ─────
    def _map_order(
        self,
        cfg: MapperConfig,
        event: SignalEvent,
        snap: AccountSnapshot,
    ) -> list[OrderIntent]:
        sym = event.symbol
        if sym is None or not self._symbol_allowed(cfg, sym):
            return []
        src_side: Optional[Side] = event.side  # type: ignore[assignment]
        if src_side is None:
            return []
        mapped_side = self._mapped_side(cfg, src_side)
        if mapped_side is None:
            return []

        action = event.action or "open"
        qty_delta = event.qty_delta or Decimal("0")
        if qty_delta <= 0 and action != "close":
            return []

        # synthesise a "PositionItem" describing the source trader's leg
        synthetic = PositionItem(
            symbol=sym,
            side=src_side,
            qty=qty_delta if action in ("open", "increase") else Decimal("0"),
            entry_px=event.px or Decimal("0"),
            unrealized_pnl=Decimal("0"),
        )

        if action in ("open", "increase"):
            qty = self._target_qty(cfg, synthetic, snap)
            if qty <= 0:
                return []
            trigger = cfg.add_trigger if action == "increase" else cfg.open_trigger
            kind, px = self._trigger_order_kind(trigger, synthetic, event)
            return [
                OrderIntent(
                    symbol=sym,
                    side=mapped_side,
                    action=action,
                    qty=qty,
                    kind=kind,
                    px=px,
                    reduce_only=False,
                    source_event_id=event.event_id,
                    leverage=cfg.leverage,
                )
            ]

        # reduce / close → mirror onto our local position
        if snap.local_position is None or snap.local_position.qty <= 0:
            return []
        local_qty = snap.local_position.qty
        if action == "close":
            close_qty = local_qty
        else:  # reduce: proportionally close based on source ratio
            src_total = (event.payload.get("source_total_qty") or Decimal("0"))
            try:
                src_total = Decimal(str(src_total))
            except Exception:  # noqa: BLE001
                src_total = Decimal("0")
            ratio = (
                (qty_delta / src_total) if src_total > 0 else Decimal("1")
            )
            close_qty = (local_qty * ratio).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
            if close_qty <= 0:
                return []
        return [
            OrderIntent(
                symbol=sym,
                side=mapped_side,
                action=action,
                qty=close_qty,
                kind="market",
                reduce_only=True,
                source_event_id=event.event_id,
                leverage=cfg.leverage,
            )
        ]

    # ───── helpers ─────
    def _symbol_allowed(self, cfg: MapperConfig, sym: str) -> bool:
        sym_u = sym.upper()
        if cfg.symbol_whitelist and sym_u not in (s.upper() for s in cfg.symbol_whitelist):
            return False
        if sym_u in (s.upper() for s in cfg.symbol_blacklist):
            return False
        return True

    def _mapped_side(self, cfg: MapperConfig, src_side: str) -> Optional[Side]:
        side: Side = "long" if src_side == "long" else "short"
        if cfg.reverse:
            side = "short" if side == "long" else "long"
        if cfg.direction_limit == "long_only" and side != "long":
            return None
        if cfg.direction_limit == "short_only" and side != "short":
            return None
        return side

    # ── core sizing logic (money_mode + multiplier) ──
    def _target_qty(
        self,
        cfg: MapperConfig,
        src_pos: PositionItem,
        snap: AccountSnapshot,
    ) -> Decimal:
        """Return the qty (in base coin units) we should hold to mirror ``src_pos``.

        Step 1: derive the **notional** USDT to deploy.
        Step 2: divide by entry/mark price to get coin qty.
        Step 3: multiply by ``multiplier``.
        Always returns a non-negative Decimal.
        """
        entry = src_pos.entry_px if src_pos.entry_px and src_pos.entry_px > 0 else snap.mark_price
        if entry is None or entry <= 0:
            return Decimal("0")

        mult = cfg.multiplier or Decimal("1")
        mode = cfg.money_mode

        if mode == "fixed":
            amt = Decimal(str(cfg.money_param.get("amount", 0)))
            if amt <= 0:
                return Decimal("0")
            notional = amt * mult
        elif mode == "full":
            pct = Decimal(str(cfg.money_param.get("percent", 0)))
            if pct <= 0:
                return Decimal("0")
            notional = snap.available_balance * (pct / Decimal("100")) * mult
        elif mode == "compound":
            pct = Decimal(str(cfg.money_param.get("percent", 0)))
            if pct <= 0:
                return Decimal("0")
            notional = snap.total_assets * (pct / Decimal("100")) * mult
        else:
            raise ValueError(f"unknown money_mode: {cfg.money_mode!r}")

        if notional <= 0:
            return Decimal("0")
        qty = notional / entry
        # round down to 8 decimal places to be conservative
        return qty.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

    # ── trigger → (kind, limit_price) ──
    def _open_order_kind(
        self, cfg: MapperConfig, src_pos: PositionItem
    ) -> tuple[OrderKind, Optional[Decimal]]:
        """Decide order kind for opening a fresh position from a snapshot."""
        return self._trigger_order_kind(cfg.open_trigger, src_pos, None)

    def _trigger_order_kind(
        self,
        trigger: dict[str, Any],
        src_pos: PositionItem,
        event: Optional[SignalEvent],
    ) -> tuple[OrderKind, Optional[Decimal]]:
        kind = (trigger or {}).get("kind", "market")
        if kind == "market":
            return "market", None

        edge_pct = Decimal(str(trigger.get("edge_pct", 0)))
        edge = edge_pct / Decimal("100")

        # avg_limit  → reference is trader's overall avg entry price
        # add_limit  → reference is the price of THIS add (event.px), if any
        if kind == "avg_limit":
            ref = src_pos.entry_px
        elif kind == "add_limit":
            ref = (event.px if event else None) or src_pos.entry_px
        else:
            return "market", None

        if ref is None or ref <= 0:
            return "market", None

        # Goal: "better than" the reference price.
        # For LONG → better == lower buy → ref * (1 - edge)
        # For SHORT → better == higher sell → ref * (1 + edge)
        if src_pos.side == "long":
            px = ref * (Decimal("1") - edge)
        else:
            px = ref * (Decimal("1") + edge)
        return "limit", px.quantize(Decimal("0.00000001"))
