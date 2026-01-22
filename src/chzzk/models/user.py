"""Pydantic models for User API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """User information returned from /users/me endpoint."""

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")

    model_config = {"populate_by_name": True}
