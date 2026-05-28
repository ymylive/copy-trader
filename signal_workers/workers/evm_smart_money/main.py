"""EVM smart-money worker.

Two parallel subscription strategies:

1. **Per-address mempool watch** — ``eth_subscribe("newPendingTransactions")``
   filtered by ``from == watched_address``. Useful for "trader X just sent
   a tx" early-warning signal; payload is opaque (we cannot decode call data
   without the contract ABI in the mempool path) so we emit a
   ``order_open`` event with ``action="open"`` and ``reason="manual"`` once
   the tx is mined.

2. **Per-contract log subscription** — ``eth_subscribe("logs", {address:
   <perpDex>, topics: [<event topic>]})`` for each perp-DEX contract in
   :mod:`contracts`. The log decoder fans out per watched-address and emits
   richer events with symbol / side / qty derived from the event payload.

The actual decoding of GMX v2 packed event data is non-trivial (it embeds
key-value pairs of mixed types); for the first cut we emit *low-fidelity*
events (symbol = "UNKNOWN-USDT-SWAP", qty_delta = "0") and leave a TODO for
a follow-up that depends on the GMX ABI we will pull at infra time.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from collections import defaultdict
from typing import Any

import orjson
import structlog
import websockets

from signal_workers.common.event_bus import EventBus
from signal_workers.common.metrics import (
    EVM_LOGS_TOTAL,
    EVM_SUBSCRIBED_ADDRESSES,
    WS_RECONNECTS_TOTAL,
)
from signal_workers.common.redis_helper import get_redis
from signal_workers.common.schema import SignalEvent, make_event_id
from signal_workers.common.trader_registry import TraderRegistry

from .contracts import PerpContract, for_chain

log = structlog.get_logger(__name__)

SUPPORTED_CHAINS = ("ethereum", "arbitrum", "optimism", "base")
REGISTRY_REFRESH_SEC = 60
RECONNECT_BASE = 1.0
RECONNECT_MAX = 60.0


def _ws_url_for_chain(chain: str) -> str | None:
    """Look up the Alchemy/QuickNode WS URL from env.

    Env key convention: ``ALCHEMY_WS_URL_ARBITRUM`` etc.  Returning ``None``
    means "no provider configured for this chain" — the worker skips it
    rather than crashing.
    """
    return os.environ.get(f"ALCHEMY_WS_URL_{chain.upper()}")


# ---------------------------------------------------------------------------
# Per-chain subscriber
# ---------------------------------------------------------------------------
class ChainSubscriber:
    def __init__(
        self,
        chain: str,
        ws_url: str,
        bus: EventBus,
        registry: TraderRegistry,
    ) -> None:
        self.chain = chain
        self.ws_url = ws_url
        self.bus = bus
        self.registry = registry
        # address (lowercase 0x) -> trader_id (== address for evm)
        self.addresses: set[str] = set()
        # subscription_id (from RPC) -> (kind, key)
        self._subs: dict[str, tuple[str, str]] = {}
        self._req_id = 1
        self._stop = asyncio.Event()
        self._pending_acks: dict[int, tuple[str, str]] = {}

    async def update_addresses(self, addrs: set[str]) -> None:
        # Normalise to lower-case to match log decoding.
        self.addresses = {a.lower() for a in addrs}
        EVM_SUBSCRIBED_ADDRESSES.labels(chain=self.chain).set(len(self.addresses))

    async def stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        backoff = RECONNECT_BASE
        while not self._stop.is_set():
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=2**22,
                ) as ws:
                    log.info("evm.connected", chain=self.chain, n_addr=len(self.addresses))
                    await self._setup_subscriptions(ws)
                    backoff = RECONNECT_BASE
                    async for raw in ws:
                        try:
                            await self._handle_frame(raw)
                        except Exception as exc:  # noqa: BLE001
                            log.warning("evm.frame_handler_err", chain=self.chain, err=str(exc))
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "evm.connection_lost", chain=self.chain, err=str(exc), backoff=backoff
                )
                WS_RECONNECTS_TOTAL.labels(source="evm_smart_money", endpoint=self.chain).inc()

            if self._stop.is_set():
                break
            await asyncio.sleep(backoff)
            backoff = min(RECONNECT_MAX, backoff * 2)

    async def _setup_subscriptions(self, ws) -> None:
        # 1) pending-tx subscription (one per chain — filter applied client side)
        await self._send(
            ws,
            method="eth_subscribe",
            params=["newPendingTransactions"],
            ack_kind=("pending_tx", "all"),
        )
        # 2) per-contract log subscription
        for c in for_chain(self.chain):
            if c.address == "0x0000000000000000000000000000000000000000":
                continue  # TODO placeholder address — skip until filled in
            await self._send(
                ws,
                method="eth_subscribe",
                params=[
                    "logs",
                    {"address": c.address, "topics": [c.topic0]},
                ],
                ack_kind=("log", c.name),
            )

    async def _send(self, ws, *, method: str, params: list[Any], ack_kind: tuple[str, str]) -> None:
        req_id = self._req_id
        self._req_id += 1
        self._pending_acks[req_id] = ack_kind
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        await ws.send(orjson.dumps(msg).decode())

    async def _handle_frame(self, raw: str | bytes) -> None:
        try:
            frame = orjson.loads(raw)
        except orjson.JSONDecodeError:
            return

        # ACK to a subscribe call
        if "id" in frame and "method" not in frame:
            sub_id = frame.get("result")
            ack = self._pending_acks.pop(frame["id"], None)
            if isinstance(sub_id, str) and ack:
                self._subs[sub_id] = ack
            return

        if frame.get("method") != "eth_subscription":
            return

        params = frame.get("params", {})
        sub_id = params.get("subscription")
        kind = self._subs.get(sub_id)
        if not kind:
            return
        result = params.get("result")

        if kind[0] == "pending_tx":
            await self._handle_pending(result)
        elif kind[0] == "log":
            await self._handle_log(result, contract_name=kind[1])

    async def _handle_pending(self, tx: Any) -> None:
        # Alchemy newPendingTransactions(full=True) gives a dict; default gives
        # just a hash. We can only emit a meaningful event in the full-object
        # variant. Skip otherwise.
        if not isinstance(tx, dict):
            return
        sender = (tx.get("from") or "").lower()
        if sender not in self.addresses:
            return
        ev = SignalEvent(
            event_id=make_event_id(
                source="evm_smart_money",
                trader_id=sender,
                kind="order_open",
                ts=int(time.time() * 1000),
                payload_key_fields={"tx": tx.get("hash", "")},
            ),
            source="evm_smart_money",
            trader_id=sender,
            trader_meta={"chain": self.chain},  # type: ignore[arg-type]
            ts=int(time.time() * 1000),
            kind="order_open",
            payload={
                "symbol": "UNKNOWN-USDT-SWAP",
                "side": "long",
                "action": "open",
                "qty_delta": "0",
                "px": "0",
                "reason": "manual",
                "tx_hash": tx.get("hash"),
                "to": tx.get("to"),
            },
        )
        await self.bus.publish(ev)

    async def _handle_log(self, lg: Any, *, contract_name: str) -> None:
        if not isinstance(lg, dict):
            return
        # Topic[1] for GMX-style events is the account address (indexed).
        topics = lg.get("topics") or []
        account = None
        if len(topics) > 1:
            t = topics[1]
            if isinstance(t, str) and t.startswith("0x") and len(t) == 66:
                # Strip 32-byte topic padding -> last 20 bytes are the address.
                account = "0x" + t[-40:].lower()
        if account is None or account not in self.addresses:
            return

        EVM_LOGS_TOTAL.labels(
            chain=self.chain, contract=contract_name, event=contract_name
        ).inc()

        # Low-fidelity event — the actual symbol/qty decode is TODO-marked
        # and depends on the contract's ABI being loaded.
        # We still emit so downstream sees activity in real time.
        action = "close" if "Decrease" in contract_name else "open"
        kind = "order_close" if action == "close" else "order_open"
        ts_ms = int(time.time() * 1000)
        ev = SignalEvent(
            event_id=make_event_id(
                source="evm_smart_money",
                trader_id=account,
                kind=kind,
                ts=ts_ms,
                payload_key_fields={
                    "txHash": lg.get("transactionHash", ""),
                    "logIndex": lg.get("logIndex", ""),
                },
            ),
            source="evm_smart_money",
            trader_id=account,
            trader_meta={"chain": self.chain},  # type: ignore[arg-type]
            ts=ts_ms,
            kind=kind,
            payload={
                "symbol": "UNKNOWN-USDT-SWAP",  # TODO decode from log.data
                "side": "long",  # TODO decode
                "action": action,
                "qty_delta": "0",  # TODO decode
                "px": "0",  # TODO decode
                "reason": "manual",
                "tx_hash": lg.get("transactionHash"),
                "log_index": lg.get("logIndex"),
                "contract": contract_name,
            },
        )
        await self.bus.publish(ev)


# ---------------------------------------------------------------------------
# Worker entry-point
# ---------------------------------------------------------------------------
async def run(args: argparse.Namespace) -> None:
    stop_event: asyncio.Event = getattr(args, "stop_event", asyncio.Event())

    redis_client = await get_redis(args.redis_url, dry_run=args.dry_run)
    bus = EventBus(redis_client)
    registry = TraderRegistry(dsn=args.database_url, source_filter="evm_smart_money")

    subscribers: dict[str, ChainSubscriber] = {}
    for chain in SUPPORTED_CHAINS:
        url = _ws_url_for_chain(chain)
        if not url:
            log.info("evm.no_provider_skipping", chain=chain)
            continue
        subscribers[chain] = ChainSubscriber(chain, url, bus, registry)

    if not subscribers:
        log.warning("evm.no_chains_configured")

    tasks: list[asyncio.Task] = [
        asyncio.create_task(s.run(), name=f"evm.{c}") for c, s in subscribers.items()
    ]

    async def _refresh_loop() -> None:
        while not stop_event.is_set():
            try:
                rows = await registry.refresh()
                by_chain: dict[str, set[str]] = defaultdict(set)
                for r in rows:
                    chain = (r.meta or {}).get("chain") or "ethereum"
                    by_chain[chain].add(r.external_id.lower())
                for chain, addrs in by_chain.items():
                    sub = subscribers.get(chain)
                    if sub:
                        await sub.update_addresses(addrs)
            except Exception as exc:  # noqa: BLE001
                log.warning("evm.refresh_failed", err=str(exc))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=REGISTRY_REFRESH_SEC)
            except asyncio.TimeoutError:
                pass

    tasks.append(asyncio.create_task(_refresh_loop(), name="evm.refresh"))

    try:
        await stop_event.wait()
    finally:
        log.info("evm.shutting_down")
        for sub in subscribers.values():
            await sub.stop()
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        await bus.aclose()
        await registry.aclose()
