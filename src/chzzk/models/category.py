"""Pydantic models for Category API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from chzzk.models.common import CategoryType


class Category(BaseModel):
    """Category information."""

    category_type: CategoryType = Field(alias="categoryType")
    category_id: str = Field(alias="categoryId")
    category_value: str = Field(alias="categoryValue")
    poster_image_url: str | None = Field(default=None, alias="posterImageUrl")

    model_config = {"populate_by_name": True}
