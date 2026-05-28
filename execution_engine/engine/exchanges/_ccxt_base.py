"""Shared CCXT-backed adapter.

The same async logic works for binance / okx / gate / bitget — only the
class name and a few flags differ. Each concrete adapter sets
``CCXT_ID`` and ``MARGIN_TYPE`` and inherits everything else.
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


def _safe_decimal(v: Any, default: str = "0") -> Decimal:
    if v is None:
        return Decimal(default)
    try:
        return Decimal(str(v))
    except Exception:  # noqa: BLE001
        return Decimal(default)


class CCXTAdapter(ExchangeAdapter):
    """Base class for adapters that talk through ccxt.async_support."""

    CCXT_ID: str = ""                       # 'binanceusdm' / 'okx' / 'gate' / 'bitget'
    DEFAULT_OPTIONS: dict[str, Any] = {}

    def __init__(
        self,
        api_key: Optional[str],
        api_secret: Optional[str],
        passphrase: Optional[str] = None,
        *,
        dry_run: bool = False,
        rate_per_sec: float = 10.0,
        **extra: Any,
    ) -> None:
        super().__init__(api_key, api_secret, passphrase, dry_run=dry_run, rate_per_sec=rate_per_sec)
        self._client: Any = None
        self._extra = extra

    # ── lazy ccxt client init ──
    def _build_client(self) -> Any:
        # imported here so the module is importable without ccxt installed
        try:
            import ccxt.async_support as ccxt  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise ExchangeError(f"ccxt not available: {exc}") from exc
        cls = getattr(ccxt, self.CCXT_ID, None)
        if cls is None:
            raise ExchangeError(f"ccxt has no exchange {self.CCXT_ID!r}")
        opts: dict[str, Any] = {
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        }
        if self.passphrase:
            opts["password"] = self.passphrase
        # merge per-class defaults + per-instance extras
        merged_options = {**self.DEFAULT_OPTIONS}
        merged_options.update(self._extra.get("options") or {})
        if merged_options:
            opts["options"] = merged_options
        return cls(opts)

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    # ── api helpers ──
    async def _call(self, fn_name: str, *args: Any, **kwargs: Any) -> Any:
        if self.dry_run:
            return self._dry_run_response(fn_name, args, kwargs)
        await self.bucket.acquire(1)
        try:
            fn = getattr(self.client, fn_name)
            return await fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            return self._reraise(exc)

    def _reraise(self, exc: BaseException) -> None:
        msg = str(exc).lower()
        if "insufficient" in msg or "balance" in msg:
            raise InsufficientBalance(str(exc)) from exc
        if "rate" in msg or "429" in msg or "too many" in msg:
            raise RateLimited(str(exc)) from exc
        if "auth" in msg or "signature" in msg or "permission" in msg or "401" in msg:
            raise AuthError(str(exc)) from exc
        raise ExchangeError(str(exc)) from exc

    def _dry_run_response(self, fn: str, args: Any, kwargs: Any) -> Any:
        """Synthetic responses used in tests."""
        if fn == "fetch_balance":
            return {"USDT": {"free": "1000", "total": "1000"}, "info": {}}
        if fn == "fetch_positions":
            return []
        if fn == "create_order":
            sym = args[0] if args else kwargs.get("symbol", "")
            return {
                "id": "dryrun-1",
                "symbol": sym,
                "side": kwargs.get("side") or (args[1] if len(args) > 1 else "buy"),
                "amount": str(kwargs.get("amount") or (args[3] if len(args) > 3 else "0")),
                "price": str(kwargs.get("price") or 0),
                "status": "closed",
                "info": {},
            }
        if fn in ("set_leverage", "set_position_mode", "cancel_order"):
            return {}
        if fn == "fetch_ticker":
            sym = args[0] if args else kwargs.get("symbol", "")
            return {"symbol": sym, "last": "65000.0"}
        return {}

    # ── ExchangeAdapter implementation ──────────────────────────────
    async def set_leverage(self, symbol: str, leverage: int) -> None:
        native = to_native(self.name, symbol)
        await self._call("set_leverage", leverage, native)

    async def set_dual_position_mode(self, on: bool) -> None:
        # ccxt exposes a unified set_position_mode for binance/bitget/okx
        try:
            await self._call("set_position_mode", on)
        except ExchangeError:
            # Older ccxt versions / exchanges may not support it
            return

    async def get_balance(self) -> Decimal:
        bal = await self._call("fetch_balance")
        usdt = (bal or {}).get("USDT") or {}
        return _safe_decimal(usdt.get("free", usdt.get("total", "0")))

    async def get_total_assets(self) -> Decimal:
        bal = await self._call("fetch_balance")
        usdt = (bal or {}).get("USDT") or {}
        total = _safe_decimal(usdt.get("total", "0"))
        # add unrealized PnL across positions
        try:
            positions = await self.get_positions()
        except ExchangeError:
            positions = []
        for p in positions:
            total += p.unrealized_pnl
        return total

    async def get_positions(self) -> list[Position]:
        raw = await self._call("fetch_positions")
        out: list[Position] = []
        for r in raw or []:
            qty = _safe_decimal(r.get("contracts") or r.get("amount") or 0)
            if qty == 0:
                continue
            side = (r.get("side") or "long").lower()
            try:
                sym = to_unified(self.name, r.get("symbol") or "")
            except ValueError:
                sym = r.get("symbol") or ""
            out.append(
                Position(
                    symbol=sym,
                    side=side,
                    qty=qty,
                    entry_px=_safe_decimal(r.get("entryPrice") or 0),
                    lev=_safe_decimal(r.get("leverage") or 1),
                    margin=_safe_decimal(r.get("initialMargin") or 0),
                    unrealized_pnl=_safe_decimal(r.get("unrealizedPnl") or 0),
                    raw=r if isinstance(r, dict) else {},
                )
            )
        return out

    async def place_order(self, intent: Any) -> OrderResult:
        native = to_native(self.name, intent.symbol)
        # long → buy, short → sell  (for opening; reduce_only flips it)
        if intent.action in ("open", "increase"):
            side = "buy" if intent.side == "long" else "sell"
        elif intent.action in ("close", "reduce"):
            # closing a LONG = sell, closing a SHORT = buy
            side = "sell" if intent.side == "long" else "buy"
        else:
            side = "buy" if intent.side == "long" else "sell"
        order_type = "market" if intent.kind == "market" else "limit"
        params: dict[str, Any] = {}
        if intent.reduce_only:
            params["reduceOnly"] = True
        price_arg = None if intent.kind == "market" else float(intent.px or 0)
        res = await self._call(
            "create_order",
            native,
            order_type,
            side,
            float(intent.qty),
            price_arg,
            params,
        )
        return OrderResult(
            exchange_order_id=str(res.get("id") or res.get("orderId") or ""),
            symbol=intent.symbol,
            side=intent.side,
            qty=_safe_decimal(res.get("amount") or intent.qty),
            px=_safe_decimal(res.get("price")) if res.get("price") else None,
            status=str(res.get("status") or "open"),
            raw=res if isinstance(res, dict) else {},
        )

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        native = to_native(self.name, symbol)
        await self._call("cancel_order", order_id, native)

    async def close_position(
        self, symbol: str, side: str, qty: Optional[Decimal] = None
    ) -> OrderResult:
        # if qty is None, fetch position
        if qty is None:
            positions = await self.get_positions()
            for p in positions:
                if p.symbol == symbol and p.side == side:
                    qty = p.qty
                    break
        if qty is None or qty <= 0:
            raise ExchangeError(f"no position to close: {symbol} {side}")
        opposite = "buy" if side == "short" else "sell"
        native = to_native(self.name, symbol)
        res = await self._call(
            "create_order",
            native,
            "market",
            opposite,
            float(qty),
            None,
            {"reduceOnly": True},
        )
        return OrderResult(
            exchange_order_id=str(res.get("id") or ""),
            symbol=symbol,
            side=side,
            qty=qty,
            px=None,
            status=str(res.get("status") or "closed"),
            raw=res if isinstance(res, dict) else {},
        )

    async def get_mark_price(self, symbol: str) -> Decimal:
        native = to_native(self.name, symbol)
        t = await self._call("fetch_ticker", native)
        return _safe_decimal(
            (t or {}).get("last")
            or (t or {}).get("close")
            or (t or {}).get("mark")
            or 0
        )

    async def close(self) -> None:
        if self._client is not None and not self.dry_run:
            try:
                await self._client.close()
            except Exception:  # noqa: BLE001
                pass
            self._client = None
