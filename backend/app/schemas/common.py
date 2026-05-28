"""Reusable Pydantic helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    """Base model: serialise from ORM attributes; allow extra=ignore."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Page(APIModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20


class MessageOut(APIModel):
    message: str = "ok"
    data: dict[str, Any] | None = None
