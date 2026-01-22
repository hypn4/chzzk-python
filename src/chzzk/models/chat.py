"""Pydantic models for Chat API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ChatAvailableCondition(StrEnum):
    """Chat available condition enumeration."""

    NONE = "NONE"
    REAL_NAME = "REAL_NAME"


class ChatAvailableGroup(StrEnum):
    """Chat available group enumeration."""

    ALL = "ALL"
    FOLLOWER = "FOLLOWER"
    MANAGER = "MANAGER"
    SUBSCRIBER = "SUBSCRIBER"


class ChatMessageResponse(BaseModel):
    """Response model for sending a chat message."""

    message_id: str = Field(alias="messageId")

    model_config = {"populate_by_name": True}


class ChatSettings(BaseModel):
    """Chat settings information."""

    chat_available_condition: ChatAvailableCondition = Field(alias="chatAvailableCondition")
    chat_available_group: ChatAvailableGroup = Field(alias="chatAvailableGroup")
    allow_subscriber_in_follower_mode: bool = Field(alias="allowSubscriberInFollowerMode")
    min_follower_minute: int = Field(alias="minFollowerMinute")
    chat_emoji_mode: bool = Field(alias="chatEmojiMode")
    chat_slow_mode_sec: int = Field(alias="chatSlowModeSec")

    model_config = {"populate_by_name": True}


class UpdateChatSettingsRequest(BaseModel):
    """Request model for updating chat settings."""

    chat_available_condition: ChatAvailableCondition | None = Field(
        default=None, serialization_alias="chatAvailableCondition"
    )
    chat_available_group: ChatAvailableGroup | None = Field(
        default=None, serialization_alias="chatAvailableGroup"
    )
    allow_subscriber_in_follower_mode: bool | None = Field(
        default=None, serialization_alias="allowSubscriberInFollowerMode"
    )
    min_follower_minute: int | None = Field(default=None, serialization_alias="minFollowerMinute")
    chat_emoji_mode: bool | None = Field(default=None, serialization_alias="chatEmojiMode")
    chat_slow_mode_sec: int | None = Field(default=None, serialization_alias="chatSlowModeSec")

    model_config = {"populate_by_name": True}
