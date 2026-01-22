"""Pydantic models for Restriction API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RestrictedChannel(BaseModel):
    """Restricted channel information."""

    restricted_channel_id: str = Field(alias="restrictedChannelId")
    restricted_channel_name: str = Field(alias="restrictedChannelName")
    release_date: datetime | None = Field(default=None, alias="releaseDate")
    created_date: datetime = Field(alias="createdDate")

    model_config = {"populate_by_name": True}
