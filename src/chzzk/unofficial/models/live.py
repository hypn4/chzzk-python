"""Live detail models for unofficial Chzzk API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LiveStatus(StrEnum):
    """Live stream status."""

    OPEN = "OPEN"
    CLOSE = "CLOSE"


class LiveDetail(BaseModel):
    """Live stream detail information.

    This model contains the detailed live information including
    the chat channel ID required for WebSocket connection.
    """

    model_config = ConfigDict(populate_by_name=True)

    live_id: int | None = Field(default=None, alias="liveId")
    live_title: str | None = Field(default=None, alias="liveTitle")
    status: LiveStatus | None = None
    live_image_url: str | None = Field(default=None, alias="liveImageUrl")
    default_thumbnail_image_url: str | None = Field(default=None, alias="defaultThumbnailImageUrl")
    concurrent_user_count: int = Field(default=0, alias="concurrentUserCount")
    accumulated_user_count: int = Field(default=0, alias="accumulatedUserCount")
    open_date: str | None = Field(default=None, alias="openDate")
    close_date: str | None = Field(default=None, alias="closeDate")
    adult: bool = False
    chat_channel_id: str | None = Field(default=None, alias="chatChannelId")
    category_type: str | None = Field(default=None, alias="categoryType")
    live_category: str | None = Field(default=None, alias="liveCategory")
    live_category_value: str | None = Field(default=None, alias="liveCategoryValue")
    chat_active: bool = Field(default=True, alias="chatActive")
    chat_available_group: str | None = Field(default=None, alias="chatAvailableGroup")
    paid_promotion: bool = Field(default=False, alias="paidPromotion")
    chat_available_condition: str | None = Field(default=None, alias="chatAvailableCondition")
    min_follower_minute: int = Field(default=0, alias="minFollowerMinute")
    channel_id: str | None = Field(default=None, alias="channelId")
    channel_name: str | None = Field(default=None, alias="channelName")
    channel_image_url: str | None = Field(default=None, alias="channelImageUrl")

    @property
    def is_live(self) -> bool:
        """Check if the channel is currently live."""
        return self.status == LiveStatus.OPEN


class LiveStatusPolling(BaseModel):
    """Live status polling response model.

    This model is used for the live-status polling endpoint which provides
    lightweight status updates for monitoring channel state changes.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: LiveStatus | None = None
    chat_channel_id: str | None = Field(default=None, alias="chatChannelId")
    live_id: int | None = Field(default=None, alias="liveId")
    live_title: str | None = Field(default=None, alias="liveTitle")
    concurrent_user_count: int = Field(default=0, alias="concurrentUserCount")
    accumulated_user_count: int = Field(default=0, alias="accumulatedUserCount")
    adult: bool = False
    category_type: str | None = Field(default=None, alias="categoryType")
    live_category: str | None = Field(default=None, alias="liveCategory")
    live_category_value: str | None = Field(default=None, alias="liveCategoryValue")
    channel_id: str | None = Field(default=None, alias="channelId")
    channel_name: str | None = Field(default=None, alias="channelName")

    @property
    def is_live(self) -> bool:
        """Check if the channel is currently live."""
        return self.status == LiveStatus.OPEN
