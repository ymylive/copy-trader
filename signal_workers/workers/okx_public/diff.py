"""Pure-Python position-diff for OKX ``public-current-subpositions`` snapshots.

OKX gives us *full* position lists per poll; to derive incremental
``order_open`` / ``order_close`` events we keep the previous snapshot in
memory and compute a structural delta.

The function is intentionally pure so ``test_okx_diff.py`` can exercise
every corner-case without any HTTP or Redis dependency.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterator

from signal_workers.common.normalizer import normalize_side, normalize_symbol
from signal_workers.common.schema import SignalEvent, make_event_id


def _key(p: dict[str, Any]) -> tuple[str, str]:
    """Stable identity for an OKX sub-position row.

    OKX `subPosId` is the canonical id, but we also key by (instId, posSide)
    in case the API recycles ids. The pair is unique within one trader.
    """
    return (str(p.get("subPosId") or ""), str(p.get("instId") or ""))


def _to_decimal(v: Any) -> Decimal:
    try:
        return Decimal(str(v))
    except (ValueError, TypeError):
        return Decimal(0)


def diff_positions(
    *,
    trader_id: str,
    trader_name: str | None,
    prev: list[dict[str, Any]] | None,
    curr: list[dict[str, Any]],
    ts_ms: int,
    received_ts_ms: int,
) -> Iterator[SignalEvent]:
    """Yield ``SignalEvent``s describing the transition from *prev* to *curr*.

    Semantics
    ---------
    * appearance of a row in *curr* not present in *prev* → ``order_open``
    * disappearance of a row in *prev* → ``order_close``
    * existing row whose ``subPos`` (size) changed:

      - ``|new| > |old|`` → ``order_open`` with action="increase"
      - ``|new| < |old|`` → ``order_close`` with action="reduce"

    The function never emits ``position_snapshot`` here — that is produced
    separately at full poll cadence by the worker.
    """
    prev_map = {_key(p): p for p in (prev or [])}
    curr_map = {_key(p): p for p in curr}

    # --- closes (gone or shrunk) -------------------------------------------------
    for k, old in prev_map.items():
        new = curr_map.get(k)
        if new is None:
            # Fully closed.
            yield _emit(
                trader_id=trader_id,
                trader_name=trader_name,
                row=old,
                action="close",
                kind="order_close",
                qty_delta=str(abs(_to_decimal(old.get("subPos")))),
                px=str(old.get("markPx") or old.get("openAvgPx") or "0"),
                ts_ms=ts_ms,
                received_ts_ms=received_ts_ms,
            )
        else:
            old_sz = abs(_to_decimal(old.get("subPos")))
            new_sz = abs(_to_decimal(new.get("subPos")))
            if new_sz < old_sz:
                yield _emit(
                    trader_id=trader_id,
                    trader_name=trader_name,
                    row=new,
                    action="reduce",
                    kind="order_close",
                    qty_delta=str(old_sz - new_sz),
                    px=str(new.get("markPx") or new.get("openAvgPx") or "0"),
                    ts_ms=ts_ms,
                    received_ts_ms=received_ts_ms,
                )

    # --- opens (new or grown) ----------------------------------------------------
    for k, new in curr_map.items():
        old = prev_map.get(k)
        if old is None:
            yield _emit(
                trader_id=trader_id,
                trader_name=trader_name,
                row=new,
                action="open",
                kind="order_open",
                qty_delta=str(abs(_to_decimal(new.get("subPos")))),
                px=str(new.get("openAvgPx") or new.get("markPx") or "0"),
                ts_ms=ts_ms,
                received_ts_ms=received_ts_ms,
            )
        else:
            old_sz = abs(_to_decimal(old.get("subPos")))
            new_sz = abs(_to_decimal(new.get("subPos")))
            if new_sz > old_sz:
                yield _emit(
                    trader_id=trader_id,
                    trader_name=trader_name,
                    row=new,
                    action="increase",
                    kind="order_open",
                    qty_delta=str(new_sz - old_sz),
                    px=str(new.get("markPx") or new.get("openAvgPx") or "0"),
                    ts_ms=ts_ms,
                    received_ts_ms=received_ts_ms,
                )


def _emit(
    *,
    trader_id: str,
    trader_name: str | None,
    row: dict[str, Any],
    action: str,
    kind: str,
    qty_delta: str,
    px: str,
    ts_ms: int,
    received_ts_ms: int,
) -> SignalEvent:
    symbol = normalize_symbol(str(row.get("instId") or ""), source="okx_public")
    side = normalize_side(str(row.get("posSide") or "long"))
    payload = {
        "symbol": symbol,
        "side": side,
        "action": action,
        "qty_delta": qty_delta,
        "px": px,
        "reason": "manual",
    }
    return SignalEvent(
        event_id=make_event_id(
            source="okx_public",
            trader_id=trader_id,
            kind=kind,
            ts=ts_ms,
            payload_key_fields={
                "symbol": symbol,
                "side": side,
                "action": action,
                "qty_delta": qty_delta,
                "subPosId": row.get("subPosId", ""),
            },
        ),
        source="okx_public",
        trader_id=trader_id,
        trader_name=trader_name,
        trader_meta={"exchange": "OKX", "is_lead": True},  # type: ignore[arg-type]
        ts=ts_ms,
        received_ts=received_ts_ms,
        kind=kind,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# Full snapshot helper (used periodically alongside the diff stream)
# ---------------------------------------------------------------------------
def build_snapshot_event(
    *,
    trader_id: str,
    trader_name: str | None,
    curr: list[dict[str, Any]],
    ts_ms: int,
    received_ts_ms: int,
) -> SignalEvent:
    rows = []
    for p in curr:
        try:
            rows.append(
                {
                    "symbol": normalize_symbol(str(p.get("instId") or ""), source="okx_public"),
                    "side": normalize_side(str(p.get("posSide") or "long")),
                    "qty": str(abs(_to_decimal(p.get("subPos")))),
                    "entry_px": str(p.get("openAvgPx") or "0"),
                    "lev": str(p.get("lever") or "1"),
                    "margin": str(p.get("margin") or "0"),
                    "unrealized_pnl": str(p.get("upl") or "0"),
                }
            )
        except Exception:  # noqa: BLE001
            continue
    return SignalEvent(
        event_id=make_event_id(
            source="okx_public",
            trader_id=trader_id,
            kind="position_snapshot",
            ts=ts_ms,
            payload_key_fields={"n": len(rows)},
        ),
        source="okx_public",
        trader_id=trader_id,
        trader_name=trader_name,
        trader_meta={"exchange": "OKX", "is_lead": True},  # type: ignore[arg-type]
        ts=ts_ms,
        received_ts=received_ts_ms,
        kind="position_snapshot",
        payload={"positions": rows},
    )
