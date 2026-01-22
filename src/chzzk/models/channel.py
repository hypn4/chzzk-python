"""Pydantic models for Channel API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    """User role enumeration for channel management."""

    STREAMING_CHANNEL_OWNER = "STREAMING_CHANNEL_OWNER"
    STREAMING_CHANNEL_MANAGER = "STREAMING_CHANNEL_MANAGER"
    STREAMING_CHAT_MANAGER = "STREAMING_CHAT_MANAGER"
    STREAMING_SETTLEMENT_MANAGER = "STREAMING_SETTLEMENT_MANAGER"


class SubscriberSortType(StrEnum):
    """Sort type enumeration for subscriber list."""

    RECENT = "RECENT"
    LONGER = "LONGER"


class ChannelInfo(BaseModel):
    """Channel information."""

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    channel_image_url: str | None = Field(default=None, alias="channelImageUrl")
    follower_count: int = Field(alias="followerCount")
    verified_mark: bool = Field(alias="verifiedMark")

    model_config = {"populate_by_name": True}


class ChannelManager(BaseModel):
    """Channel manager information."""

    manager_channel_id: str = Field(alias="managerChannelId")
    manager_channel_name: str = Field(alias="managerChannelName")
    user_role: UserRole = Field(alias="userRole")
    created_date: datetime = Field(alias="createdDate")

    model_config = {"populate_by_name": True}


class Follower(BaseModel):
    """Follower information."""

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    created_date: datetime = Field(alias="createdDate")

    model_config = {"populate_by_name": True}


class Subscriber(BaseModel):
    """Subscriber information."""

    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    created_date: datetime = Field(alias="createdDate")
    tier_no: int = Field(alias="tierNo")
    month: int

    model_config = {"populate_by_name": True}
