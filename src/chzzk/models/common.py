"""Common models shared across API modules."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class Page(BaseModel):
    """Pagination information for list responses."""

    next: str | None = None

    model_config = {"populate_by_name": True}


class CategoryType(StrEnum):
    """Category type enumeration."""

    GAME = "GAME"
    SPORTS = "SPORTS"
    ETC = "ETC"
