"""Pydantic models for Live API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from chzzk.models.common import CategoryType, Page


class LiveInfo(BaseModel):
    """Live broadcast information."""

    live_id: int = Field(alias="liveId")
    live_title: str = Field(alias="liveTitle")
    live_thumbnail_image_url: str | None = Field(default=None, alias="liveThumbnailImageUrl")
    concurrent_user_count: int = Field(alias="concurrentUserCount")
    open_date: datetime = Field(alias="openDate")
    adult: bool
    tags: list[str] = Field(default_factory=list)
    category_type: CategoryType | None = Field(default=None, alias="categoryType")
    live_category: str | None = Field(default=None, alias="liveCategory")
    live_category_value: str | None = Field(default=None, alias="liveCategoryValue")
    channel_id: str = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")
    channel_image_url: str | None = Field(default=None, alias="channelImageUrl")

    model_config = {"populate_by_name": True}


class LiveListResponse(BaseModel):
    """Response model for live list endpoint."""

    data: list[LiveInfo]
    page: Page

    model_config = {"populate_by_name": True}


class StreamKey(BaseModel):
    """Stream key information."""

    stream_key: str = Field(alias="streamKey")

    model_config = {"populate_by_name": True}


class LiveSettingCategory(BaseModel):
    """Category information in live setting."""

    category_type: CategoryType = Field(alias="categoryType")
    category_id: str = Field(alias="categoryId")
    category_value: str = Field(alias="categoryValue")
    poster_image_url: str | None = Field(default=None, alias="posterImageUrl")

    model_config = {"populate_by_name": True}


class LiveSetting(BaseModel):
    """Live broadcast setting information."""

    default_live_title: str | None = Field(default=None, alias="defaultLiveTitle")
    category: LiveSettingCategory | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class UpdateLiveSettingRequest(BaseModel):
    """Request model for updating live setting."""

    default_live_title: str | None = Field(default=None, serialization_alias="defaultLiveTitle")
    category_type: CategoryType | None = Field(default=None, serialization_alias="categoryType")
    category_id: str | None = Field(default=None, serialization_alias="categoryId")
    tags: list[str] | None = None

    model_config = {"populate_by_name": True}
