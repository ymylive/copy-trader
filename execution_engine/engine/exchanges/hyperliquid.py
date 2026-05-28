"""Hyperliquid perpetual adapter.

Hyperliquid is on-chain — orders are signed by the user's wallet
private key (or an "agent" key) and submitted to the protocol's REST
API. We use ``hyperliquid-python-sdk``:

    pip install hyperliquid-python-sdk

Public reads (positions, mark price) go through :class:`Info`; private
trades through :class:`Exchange`. To stay testable and to avoid forcing
private-key gymnastics in unit tests, the adapter falls back to a stub
when ``dry_run=True`` or when no key is configured.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Optional

from ..symbols import to_native, to_unified
from .base import (
    AuthError,
    ExchangeAdapter,
    ExchangeError,
    InsufficientBalance,
    OrderResult,
    Position,
    RateLimited,
)

MAINNET_API_URL = "https://api.hyperliquid.xyz"


def _safe_decimal(v: Any, default: str = "0") -> Decimal:
    if v is None:
        return Decimal(default)
    try:
        return Decimal(str(v))
    except Exception:  # noqa: BLE001
        return Decimal(default)


class HyperliquidAdapter(ExchangeAdapter):
    name = "hyperliquid"

    def __init__(
        self,
        wallet_address: Optional[str] = None,
        wallet_private_key: Optional[str] = None,
        *,
        dry_run: bool = False,
        rate_per_sec: float = 50.0,
        base_url: str = MAINNET_API_URL,
        **extra: Any,
    ) -> None:
        # Note: api_key/secret in ExchangeAdapter.__init__ map to
        # wallet_address / wallet_private_key.
        super().__init__(
            api_key=wallet_address,
            api_secret=wallet_private_key,
            passphrase=None,
            dry_run=dry_run,
            rate_per_sec=rate_per_sec,
        )
        self.wallet_address = wallet_address
        self.wallet_private_key = wallet_private_key
        self.base_url = base_url
        self._info: Any = None
        self._exchange: Any = None
        self._extra = extra

    # ── lazy SDK init ─────────────────────────────────────────────────
    def _init_sdk(self) -> tuple[Any, Any]:
        try:
            from hyperliquid.info import Info  # type: ignore
            from hyperliquid.exchange import Exchange  # type: ignore
            from eth_account import Account  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise ExchangeError(f"hyperliquid SDK not available: {exc}") from exc
        info = Info(self.base_url, skip_ws=True)
        if self.wallet_private_key:
            wallet = Account.from_key(self.wallet_private_key)
            exchange = Exchange(wallet, self.base_url, account_address=self.wallet_address)
        else:
            exchange = None
        return info, exchange

    @property
    def info(self) -> Any:
        if self._info is None:
            self._info, self._exchange = self._init_sdk()
        return self._info

    @property
    def exchange(self) -> Any:
        if self._exchange is None:
            self._info, self._exchange = self._init_sdk()
        if self._exchange is None:
            raise AuthError("Hyperliquid: no private key configured")
        return self._exchange

    # ── sync→async bridge (hyperliquid SDK is sync) ───────────────────
    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        await self.bucket.acquire(1)
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).lower()
            if "insufficient" in msg or "margin" in msg:
                raise InsufficientBalance(str(exc)) from exc
            if "rate" in msg or "429" in msg:
                raise RateLimited(str(exc)) from exc
            raise ExchangeError(str(exc)) from exc

    # ── ExchangeAdapter implementation ────────────────────────────────
    async def set_leverage(self, symbol: str, leverage: int) -> None:
        if self.dry_run or not self.wallet_private_key:
            return
        coin = to_native(self.name, symbol)
        await self._run(self.exchange.update_leverage, leverage, coin, True)

    async def set_dual_position_mode(self, on: bool) -> None:
        # Hyperliquid uses one-way mode only — no-op.
        return

    async def get_balance(self) -> Decimal:
        if self.dry_run or not self.wallet_address:
            return Decimal("1000")
        state = await self._run(self.info.user_state, self.wallet_address)
        # margin summary lives in crossMarginSummary
        ms = (state or {}).get("crossMarginSummary") or {}
        return _safe_decimal(ms.get("accountValue", "0")) - _safe_decimal(
            ms.get("totalMarginUsed", "0")
        )

    async def get_total_assets(self) -> Decimal:
        if self.dry_run or not self.wallet_address:
            return Decimal("1000")
        state = await self._run(self.info.user_state, self.wallet_address)
        ms = (state or {}).get("crossMarginSummary") or {}
        return _safe_decimal(ms.get("accountValue", "0"))

    async def get_positions(self) -> list[Position]:
        if self.dry_run or not self.wallet_address:
            return []
        state = await self._run(self.info.user_state, self.wallet_address)
        out: list[Position] = []
        for ap in (state or {}).get("assetPositions") or []:
            pos = ap.get("position") or {}
            sz = _safe_decimal(pos.get("szi", "0"))
            if sz == 0:
                continue
            side = "long" if sz > 0 else "short"
            qty = abs(sz)
            coin = pos.get("coin") or ""
            try:
                sym = to_unified(self.name, coin)
            except ValueError:
                sym = f"{coin}-USD-SWAP"
            out.append(
                Position(
                    symbol=sym,
                    side=side,
                    qty=qty,
                    entry_px=_safe_decimal(pos.get("entryPx", "0")),
                    lev=_safe_decimal((pos.get("leverage") or {}).get("value", "1")),
                    margin=_safe_decimal(pos.get("marginUsed", "0")),
                    unrealized_pnl=_safe_decimal(pos.get("unrealizedPnl", "0")),
                    raw=pos,
                )
            )
        return out

    async def place_order(self, intent: Any) -> OrderResult:
        if self.dry_run or not self.wallet_private_key:
            return OrderResult(
                exchange_order_id="hl-dryrun-1",
                symbol=intent.symbol,
                side=intent.side,
                qty=intent.qty,
                px=intent.px,
                status="filled",
                raw={"dry_run": True},
            )
        coin = to_native(self.name, intent.symbol)
        is_buy = intent.side == "long"
        if intent.action in ("close", "reduce"):
            is_buy = not is_buy
        # Hyperliquid SDK signature: order(coin, is_buy, sz, limit_px, order_type, reduce_only)
        order_type: dict[str, Any]
        if intent.kind == "market":
            # SDK uses Ioc/Gtc; market = aggressive Ioc with px = best
            order_type = {"limit": {"tif": "Ioc"}}
            px = float(intent.px or 0) or (
                float(await self.get_mark_price(intent.symbol)) * (1.01 if is_buy else 0.99)
            )
        else:
            order_type = {"limit": {"tif": "Gtc"}}
            px = float(intent.px or 0)

        res = await self._run(
            self.exchange.order,
            coin,
            is_buy,
            float(intent.qty),
            px,
            order_type,
            intent.reduce_only,
        )
        status = "open"
        order_id = ""
        try:
            statuses = (res.get("response") or {}).get("data", {}).get("statuses", [])
            if statuses:
                s = statuses[0]
                if "resting" in s:
                    order_id = str(s["resting"]["oid"])
                    status = "open"
                elif "filled" in s:
                    order_id = str(s["filled"]["oid"])
                    status = "filled"
        except Exception:  # noqa: BLE001
            pass
        return OrderResult(
            exchange_order_id=order_id,
            symbol=intent.symbol,
            side=intent.side,
            qty=intent.qty,
            px=Decimal(str(px)),
            status=status,
            raw=res if isinstance(res, dict) else {},
        )

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        if self.dry_run or not self.wallet_private_key:
            return
        coin = to_native(self.name, symbol)
        await self._run(self.exchange.cancel, coin, int(order_id))

    async def close_position(
        self, symbol: str, side: str, qty: Optional[Decimal] = None
    ) -> OrderResult:
        if qty is None:
            positions = await self.get_positions()
            for p in positions:
                if p.symbol == symbol and p.side == side:
                    qty = p.qty
                    break
        if qty is None or qty <= 0:
            raise ExchangeError(f"no position to close: {symbol} {side}")

        from ..position_mapper import OrderIntent  # local import to avoid cycle

        intent = OrderIntent(
            symbol=symbol,
            side=side,                 # mapper still treats it as the original direction
            action="close",
            qty=qty,
            kind="market",
            reduce_only=True,
        )
        return await self.place_order(intent)

    async def get_mark_price(self, symbol: str) -> Decimal:
        if self.dry_run:
            return Decimal("65000")
        coin = to_native(self.name, symbol)
        ctxs = await self._run(self.info.meta_and_asset_ctxs)
        try:
            meta, asset_ctxs = ctxs
            for u, ctx in zip(meta.get("universe", []), asset_ctxs):
                if u.get("name") == coin:
                    return _safe_decimal(ctx.get("markPx") or ctx.get("midPx") or 0)
        except Exception:  # noqa: BLE001
            pass
        return Decimal("0")
