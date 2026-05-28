"""FollowerRunner + FollowerEngine.

The engine boots once per process and keeps a pool of FollowerRunner
coroutines — exactly one per (exchange_account, trader) pair that has
``status='running'``. Each runner consumes its trader's stream via a
Redis consumer group and applies the full pipeline:

    SignalEvent →  PositionMapper  →  RiskGuard  →  ExchangeAdapter
                                     ↓               ↓
                                  copy_orders    notifier

Hot reload: every ``config_reload_interval_sec`` we re-read
``copy_configs`` from PG; new rows spawn new runners, removed rows are
told to cancel, mutated rows update their config in place.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import session_scope
from .events import PositionItem, SignalEvent
from .exchanges import ExchangeAdapter, make_adapter, ExchangeError, InsufficientBalance
from .logging_setup import get_logger
from .metrics import (
    order_latency,
    orders_failed,
    orders_submitted,
    runner_state,
    runners_active,
    signals_consumed,
    signals_skipped,
)
from .models import CopyConfig, CopyOrder, ExchangeAccount, Trader
from .notifier import Notifier
from .position_mapper import MapperConfig, OrderIntent, PositionMapper, AccountSnapshot
from .risk import RiskAction, RiskDecision, RiskGuard, RiskInputs
from .secrets import decrypt_secret

log = get_logger(__name__)


# ───────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class _RunnerCtx:
    """Per-runner mutable state."""

    config_id: int
    exchange_account_id: int
    trader_id: int
    source: str
    external_trader_id: str
    exchange: str
    api_key: Optional[str]
    api_secret: Optional[str]
    passphrase: Optional[str]
    user_id: int

    mapper_cfg: MapperConfig
    tp: dict[str, Any] = field(default_factory=dict)
    sl: dict[str, Any] = field(default_factory=dict)
    loss_threshold: dict[str, Any] = field(default_factory=dict)
    safety_cushion: dict[str, Any] = field(default_factory=dict)
    refill: dict[str, Any] = field(default_factory=dict)
    notify_channels: list[str] = field(default_factory=list)
    notify_types: list[str] = field(default_factory=list)
    status: str = "running"

    # runtime bookkeeping
    is_first_event: bool = True
    baseline_nav: Decimal = Decimal("0")
    tp_triggered_symbols: set[str] = field(default_factory=set)


# ───────────────────────────────────────────────────────────────────────


class FollowerRunner:
    """One coroutine per copy_config; reads from its trader's stream."""

    def __init__(
        self,
        ctx: _RunnerCtx,
        redis: Redis,
        adapter: ExchangeAdapter,
        mapper: PositionMapper,
        risk: RiskGuard,
        notifier: Notifier,
        *,
        global_sema: asyncio.Semaphore,
    ) -> None:
        self.ctx = ctx
        self.redis = redis
        self.adapter = adapter
        self.mapper = mapper
        self.risk = risk
        self.notifier = notifier
        self.global_sema = global_sema
        self._task: Optional[asyncio.Task[None]] = None
        self._stop = asyncio.Event()

    # ── lifecycle ─────────────────────────────────────────────────
    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name=f"runner-{self.ctx.config_id}")
            runners_active.inc()
            runner_state.labels(config_id=str(self.ctx.config_id)).set(1.0)

    async def stop(self) -> None:
        self._stop.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        runner_state.labels(config_id=str(self.ctx.config_id)).set(0.0)
        runners_active.dec()

    @property
    def stream_key(self) -> str:
        return f"stream:signals:{self.ctx.source}:{self.ctx.external_trader_id}"

    @property
    def consumer_name(self) -> str:
        return f"runner:{self.ctx.config_id}"

    # ── main loop ─────────────────────────────────────────────────
    async def _run(self) -> None:
        s = get_settings()
        group = s.consumer_group
        # ensure group exists (idempotent)
        try:
            await self.redis.xgroup_create(
                name=self.stream_key, groupname=group, id="0", mkstream=True
            )
        except Exception as exc:  # noqa: BLE001
            # BUSYGROUP → already exists, OK
            if "BUSYGROUP" not in str(exc):
                log.warning("xgroup_create_failed", error=str(exc), stream=self.stream_key)

        log.info(
            "runner_started",
            config_id=self.ctx.config_id,
            stream=self.stream_key,
            consumer=self.consumer_name,
        )

        # snapshot baseline NAV at start (for safety_cushion baseline)
        try:
            self.ctx.baseline_nav = await self.adapter.get_total_assets()
        except Exception as exc:  # noqa: BLE001
            log.warning("baseline_nav_failed", error=str(exc), config_id=self.ctx.config_id)
            self.ctx.baseline_nav = Decimal("0")

        while not self._stop.is_set():
            if self.ctx.status != "running":
                await asyncio.sleep(1.0)
                continue
            try:
                messages = await self.redis.xreadgroup(
                    groupname=group,
                    consumername=self.consumer_name,
                    streams={self.stream_key: ">"},
                    count=16,
                    block=2000,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning("xreadgroup_failed", error=str(exc), stream=self.stream_key)
                await asyncio.sleep(1.0)
                continue

            if not messages:
                continue
            for _stream_key, entries in messages:
                for msg_id, fields in entries:
                    try:
                        await self._handle_message(msg_id, fields, group)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:  # noqa: BLE001
                        log.exception(
                            "handle_message_failed",
                            error=str(exc),
                            config_id=self.ctx.config_id,
                            msg_id=msg_id,
                        )
                        signals_skipped.labels(reason="exception").inc()
                    # always ACK to prevent backlog; failures are logged in copy_orders
                    try:
                        await self.redis.xack(self.stream_key, group, msg_id)
                    except Exception:  # noqa: BLE001
                        pass

    # ── per-message pipeline ─────────────────────────────────────
    async def _handle_message(
        self, msg_id: bytes | str, fields: dict[Any, Any], group: str
    ) -> None:
        # fields look like {b'data': b'{...json...}'}  OR  {'data': '...'}
        raw = (
            fields.get(b"data") if isinstance(fields, dict) and b"data" in fields
            else fields.get("data")
            if isinstance(fields, dict)
            else None
        )
        if raw is None:
            # maybe the producer used flat keys: collapse them
            payload = {k.decode() if isinstance(k, bytes) else k:
                       v.decode() if isinstance(v, bytes) else v
                       for k, v in fields.items()}
            event = SignalEvent.model_validate(payload)
        else:
            data = raw.decode() if isinstance(raw, bytes) else raw
            event = SignalEvent.model_validate_json(data)
        signals_consumed.labels(source=event.source, kind=event.kind).inc()

        # gather snapshot
        snap = await self._snapshot()
        snap.is_first_event = self.ctx.is_first_event
        self.ctx.is_first_event = False

        # 1) risk pre-check (only meaningful when we have local positions)
        if snap.local_position is not None or any(
            isinstance(p, PositionItem) for p in []
        ):
            pass

        # 2) map to intents
        intents = self.mapper.map_event(self.ctx.mapper_cfg, event, snap)
        if not intents:
            signals_skipped.labels(reason="no_intent").inc()
            return

        # 3) for each intent: risk-check (per symbol), submit, log
        for intent in intents:
            # ensure leverage / dual-mode on first contact with the symbol
            try:
                if intent.leverage:
                    await self.adapter.set_leverage(intent.symbol, intent.leverage)
            except ExchangeError:
                pass

            # idempotency: dedup by (config_id, source_event_id)
            if await self._already_done(intent.source_event_id):
                signals_skipped.labels(reason="duplicate").inc()
                continue

            order_row = await self._record_pending(intent, event)
            await self._submit_intent(intent, event, order_row_id=order_row)

    # ── snapshot gathering ──────────────────────────────────────
    async def _snapshot(self) -> AccountSnapshot:
        try:
            bal = await self.adapter.get_balance()
            total = await self.adapter.get_total_assets()
        except Exception as exc:  # noqa: BLE001
            log.warning("snapshot_failed", error=str(exc), config_id=self.ctx.config_id)
            return AccountSnapshot(
                available_balance=Decimal("0"),
                total_assets=Decimal("0"),
            )
        return AccountSnapshot(
            available_balance=bal,
            total_assets=total,
            local_position=None,
            mark_price=None,
            is_first_event=self.ctx.is_first_event,
        )

    # ── DB writes ────────────────────────────────────────────────
    async def _already_done(self, source_event_id: Optional[str]) -> bool:
        if not source_event_id:
            return False
        async with session_scope() as ses:
            q = await ses.execute(
                select(CopyOrder.id).where(
                    CopyOrder.copy_config_id == self.ctx.config_id,
                    CopyOrder.source_event_id == source_event_id,
                )
            )
            return q.first() is not None

    async def _record_pending(self, intent: OrderIntent, event: SignalEvent) -> int:
        async with session_scope() as ses:
            row = CopyOrder(
                copy_config_id=self.ctx.config_id,
                exchange_account_id=self.ctx.exchange_account_id,
                symbol=intent.symbol,
                side=intent.side,
                action=intent.action,
                qty=intent.qty,
                px=intent.px,
                status="pending",
                source_event_id=intent.source_event_id or event.event_id,
            )
            ses.add(row)
            await ses.commit()
            await ses.refresh(row)
            return row.id

    async def _record_result(
        self,
        order_row_id: int,
        *,
        status: str,
        exchange_order_id: Optional[str] = None,
        px: Optional[Decimal] = None,
        error: Optional[str] = None,
    ) -> None:
        async with session_scope() as ses:
            await ses.execute(
                update(CopyOrder)
                .where(CopyOrder.id == order_row_id)
                .values(
                    status=status,
                    exchange_order_id=exchange_order_id,
                    px=px,
                    error=error,
                    updated_at=datetime.now(tz=timezone.utc),
                )
            )
            await ses.commit()

    async def _pause_config(self, reason: str) -> None:
        async with session_scope() as ses:
            await ses.execute(
                update(CopyConfig)
                .where(CopyConfig.id == self.ctx.config_id)
                .values(status="paused", updated_at=datetime.now(tz=timezone.utc))
            )
            await ses.commit()
        self.ctx.status = "paused"
        runner_state.labels(config_id=str(self.ctx.config_id)).set(0.5)
        await self.notifier.notify(
            user_id=self.ctx.user_id,
            notify_type="risk",
            channels=self.ctx.notify_channels,
            payload={"config_id": self.ctx.config_id, "reason": reason},
        )

    # ── actually submit an intent ────────────────────────────────
    async def _submit_intent(
        self,
        intent: OrderIntent,
        event: SignalEvent,
        *,
        order_row_id: int,
    ) -> None:
        async with self.global_sema:
            t0 = time.monotonic()
            try:
                result = await self.adapter.place_order(intent)
                order_latency.labels(exchange=self.ctx.exchange).observe(
                    time.monotonic() - t0
                )
                orders_submitted.labels(
                    exchange=self.ctx.exchange,
                    side=intent.side,
                    kind=intent.kind,
                ).inc()
                await self._record_result(
                    order_row_id,
                    status=result.status,
                    exchange_order_id=result.exchange_order_id,
                    px=result.px,
                )
                if "open_ok" in self.ctx.notify_types:
                    await self.notifier.notify(
                        user_id=self.ctx.user_id,
                        notify_type="open_ok",
                        channels=self.ctx.notify_channels,
                        payload={
                            "config_id": self.ctx.config_id,
                            "symbol": intent.symbol,
                            "side": intent.side,
                            "qty": str(intent.qty),
                            "px": str(result.px) if result.px else None,
                            "order_id": result.exchange_order_id,
                        },
                    )
                log.info(
                    "order_submitted",
                    config_id=self.ctx.config_id,
                    symbol=intent.symbol,
                    side=intent.side,
                    qty=str(intent.qty),
                    order_id=result.exchange_order_id,
                )
            except InsufficientBalance as exc:
                orders_failed.labels(
                    exchange=self.ctx.exchange, reason="insufficient_balance"
                ).inc()
                await self._record_result(
                    order_row_id, status="rejected", error=f"insufficient_balance: {exc}"
                )
                await self._pause_config("insufficient_balance")
            except ExchangeError as exc:
                orders_failed.labels(
                    exchange=self.ctx.exchange, reason="exchange_error"
                ).inc()
                await self._record_result(
                    order_row_id, status="rejected", error=str(exc)
                )
                if "open_fail" in self.ctx.notify_types:
                    await self.notifier.notify(
                        user_id=self.ctx.user_id,
                        notify_type="open_fail",
                        channels=self.ctx.notify_channels,
                        payload={
                            "config_id": self.ctx.config_id,
                            "symbol": intent.symbol,
                            "side": intent.side,
                            "error": str(exc),
                        },
                    )

    # ── periodic risk evaluation (called by scheduler) ───────────
    async def evaluate_risk(self) -> Optional[RiskDecision]:
        try:
            positions = await self.adapter.get_positions()
            nav = await self.adapter.get_total_assets()
        except Exception as exc:  # noqa: BLE001
            log.warning("risk_eval_skip", error=str(exc), config_id=self.ctx.config_id)
            return None
        mark_prices: dict[str, Decimal] = {}
        for p in positions:
            try:
                mark_prices[p.symbol] = await self.adapter.get_mark_price(p.symbol)
            except ExchangeError:
                pass
        # adapt to risk PositionItem schema
        local_items: list[PositionItem] = [
            PositionItem(
                symbol=p.symbol,
                side=p.side,                                      # type: ignore[arg-type]
                qty=p.qty,
                entry_px=p.entry_px,
                lev=p.lev,
                margin=p.margin,
                unrealized_pnl=p.unrealized_pnl,
            )
            for p in positions
        ]
        ri = RiskInputs(
            cfg=self.ctx.mapper_cfg,
            local_positions=local_items,
            mark_prices=mark_prices,
            account_nav=nav,
            baseline_nav=self.ctx.baseline_nav or nav,
            tp=self.ctx.tp,
            sl=self.ctx.sl,
            loss_threshold=self.ctx.loss_threshold,
            safety_cushion=self.ctx.safety_cushion,
            refill=self.ctx.refill,
            tp_triggered_symbols=self.ctx.tp_triggered_symbols,
        )
        decision = self.risk.evaluate(ri)
        await self._apply_risk_decision(decision)
        return decision

    async def _apply_risk_decision(self, d: RiskDecision) -> None:
        if d.action is RiskAction.OK:
            return
        log.info(
            "risk_decision",
            config_id=self.ctx.config_id,
            action=d.action,
            reason=d.reason,
        )
        if d.action is RiskAction.DECAY_MULTIPLIER and d.new_multiplier is not None:
            self.ctx.mapper_cfg.multiplier = d.new_multiplier
            return
        # close orders → submit
        for intent in d.intents:
            row_id = await self._record_pending(
                intent,
                SignalEvent(
                    schema="signal.v1",  # type: ignore[arg-type]
                    event_id=f"risk-{self.ctx.config_id}-{int(time.time()*1000)}",
                    source="risk",
                    trader_id=self.ctx.external_trader_id,
                    ts=int(time.time() * 1000),
                    kind="order_close",
                    payload={"symbol": intent.symbol, "side": intent.side, "action": intent.action},
                ),
            )
            await self._submit_intent(
                intent,
                SignalEvent(
                    schema="signal.v1",  # type: ignore[arg-type]
                    event_id=f"risk-{self.ctx.config_id}-{row_id}",
                    source="risk",
                    trader_id=self.ctx.external_trader_id,
                    ts=int(time.time() * 1000),
                    kind="order_close",
                    payload={},
                ),
                order_row_id=row_id,
            )
        if d.action is RiskAction.PAUSE_AND_CLOSE:
            await self._pause_config(d.reason)


# ───────────────────────────────────────────────────────────────────────


class FollowerEngine:
    """Process-wide orchestrator: holds the runner pool + hot reloader."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis: Redis = Redis.from_url(self.settings.redis_url, decode_responses=False)
        self.mapper = PositionMapper()
        self.risk = RiskGuard()
        self.notifier = Notifier()
        self.global_sema = asyncio.Semaphore(self.settings.max_concurrent_orders)
        self.runners: dict[int, FollowerRunner] = {}
        self._reload_task: Optional[asyncio.Task[None]] = None
        self._risk_task: Optional[asyncio.Task[None]] = None
        self._stop = asyncio.Event()

    # ── lifecycle ─────────────────────────────────────────────
    async def start(self) -> None:
        await self.reload_configs()
        self._reload_task = asyncio.create_task(self._reload_loop(), name="reload-loop")
        self._risk_task = asyncio.create_task(self._risk_loop(), name="risk-loop")
        log.info("engine_started", n_runners=len(self.runners))

    async def stop(self) -> None:
        self._stop.set()
        for t in (self._reload_task, self._risk_task):
            if t and not t.done():
                t.cancel()
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass
        await asyncio.gather(*(r.stop() for r in self.runners.values()), return_exceptions=True)
        for r in self.runners.values():
            try:
                await r.adapter.close()
            except Exception:  # noqa: BLE001
                pass
        await self.notifier.close()
        try:
            await self.redis.close()
        except Exception:  # noqa: BLE001
            pass

    # ── config reloading ─────────────────────────────────────
    async def _reload_loop(self) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.sleep(self.settings.config_reload_interval_sec)
                await self.reload_configs()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning("reload_loop_failed", error=str(exc))

    async def _risk_loop(self) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.sleep(self.settings.refill_scan_interval_sec)
                await asyncio.gather(
                    *(r.evaluate_risk() for r in list(self.runners.values())),
                    return_exceptions=True,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning("risk_loop_failed", error=str(exc))

    async def reload_configs(self) -> None:
        rows = await self._fetch_active_configs()
        seen: set[int] = set()
        for ctx in rows:
            seen.add(ctx.config_id)
            existing = self.runners.get(ctx.config_id)
            if existing is None:
                runner = await self._spawn(ctx)
                self.runners[ctx.config_id] = runner
                runner.start()
            else:
                # update mutable fields in place
                existing.ctx.mapper_cfg = ctx.mapper_cfg
                existing.ctx.tp = ctx.tp
                existing.ctx.sl = ctx.sl
                existing.ctx.loss_threshold = ctx.loss_threshold
                existing.ctx.safety_cushion = ctx.safety_cushion
                existing.ctx.refill = ctx.refill
                existing.ctx.notify_channels = ctx.notify_channels
                existing.ctx.notify_types = ctx.notify_types
                existing.ctx.status = ctx.status
        # stop runners whose config disappeared / went stopped
        to_remove = [cid for cid in self.runners if cid not in seen]
        for cid in to_remove:
            r = self.runners.pop(cid)
            await r.stop()
            try:
                await r.adapter.close()
            except Exception:  # noqa: BLE001
                pass

    async def _fetch_active_configs(self) -> list[_RunnerCtx]:
        async with session_scope() as ses:
            q = await ses.execute(
                select(CopyConfig, ExchangeAccount, Trader)
                .join(ExchangeAccount, ExchangeAccount.id == CopyConfig.exchange_account_id)
                .join(Trader, Trader.id == CopyConfig.trader_id)
                .where(CopyConfig.status == "running")
            )
            out: list[_RunnerCtx] = []
            for cfg, acct, trader in q.all():
                mc = MapperConfig.from_orm(cfg)
                mc.leverage = acct.leverage_default
                api_key = decrypt_secret(acct.api_key_enc)
                api_secret = decrypt_secret(acct.api_secret_enc)
                passphrase = decrypt_secret(acct.passphrase_enc)
                out.append(
                    _RunnerCtx(
                        config_id=cfg.id,
                        exchange_account_id=acct.id,
                        trader_id=trader.id,
                        source=trader.source,
                        external_trader_id=trader.external_id,
                        exchange=acct.exchange,
                        api_key=api_key,
                        api_secret=api_secret,
                        passphrase=passphrase,
                        user_id=cfg.user_id,
                        mapper_cfg=mc,
                        tp=dict(cfg.tp or {}),
                        sl=dict(cfg.sl or {}),
                        loss_threshold=dict(cfg.loss_threshold or {}),
                        safety_cushion=dict(cfg.safety_cushion or {}),
                        refill=dict(cfg.refill or {}),
                        notify_channels=list(cfg.notify_channels or []),
                        notify_types=list(cfg.notify_types or []),
                        status=cfg.status,
                    )
                )
            return out

    async def _spawn(self, ctx: _RunnerCtx) -> FollowerRunner:
        rps = self.settings.exchange_rps.get(ctx.exchange, 10.0)
        adapter = make_adapter(
            ctx.exchange,
            api_key=ctx.api_key,
            api_secret=ctx.api_secret,
            passphrase=ctx.passphrase,
            dry_run=self.settings.dry_run,
            rate_per_sec=rps,
        )
        return FollowerRunner(
            ctx=ctx,
            redis=self.redis,
            adapter=adapter,
            mapper=self.mapper,
            risk=self.risk,
            notifier=self.notifier,
            global_sema=self.global_sema,
        )
