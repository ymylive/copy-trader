"""Notifier — HTTP push to the backend's internal endpoint.

We do not talk to TG / email / SMS directly; we send a small JSON
payload to ``POST {backend_internal_url}`` and let the backend fan out.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from .config import get_settings
from .logging_setup import get_logger

log = get_logger(__name__)


class Notifier:
    """Async HTTP notifier with retries."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        timeout_sec: float = 5.0,
    ) -> None:
        s = get_settings()
        self.url = url or s.backend_internal_url
        self.token = token or s.backend_internal_token
        self.timeout_sec = timeout_sec
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout_sec)
        return self._client

    async def notify(
        self,
        *,
        user_id: int,
        notify_type: str,
        channels: list[str],
        payload: dict[str, Any],
    ) -> bool:
        body = {
            "user_id": user_id,
            "type": notify_type,           # open_ok / open_fail / risk / tp_sl / margin_change
            "channels": channels,
            "payload": payload,
        }
        headers = {"X-Internal-Token": self.token}
        try:
            client = await self._get_client()
            r = await client.post(self.url, json=body, headers=headers)
            r.raise_for_status()
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("notify_failed", error=str(exc), url=self.url, type=notify_type)
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
