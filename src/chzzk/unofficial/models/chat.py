"""Chat models for unofficial Chzzk API."""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TemporaryRestrict(BaseModel):
    """Temporary restriction info."""

    model_config = ConfigDict(populate_by_name=True)

    temporary_restrict: bool = Field(default=False, alias="temporaryRestrict")
    created_time: str | None = Field(default=None, alias="createdTime")


class ChatAccessToken(BaseModel):
    """Chat access token response."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    extra_token: str = Field(alias="extraToken")
    real_name_auth: bool = Field(default=False, alias="realNameAuth")
    temporary_restrict: TemporaryRestrict | None = Field(default=None, alias="temporaryRestrict")


class ChatCmd(IntEnum):
    """Chat command types."""

    PING = 0
    PONG = 10000
    CONNECT = 100
    CONNECTED = 10100
    REQUEST_RECENT_CHAT = 5101
    RECENT_CHAT = 15101
    EVENT = 93006
    CHAT = 93101
    DONATION = 93102
    KICK = 94005
    BLOCK = 94006
    BLIND = 94008
    NOTICE = 94010
    PENALTY = 94015
    SEND_CHAT = 3101


class ChatType(StrEnum):
    """Chat message types."""

    TEXT = "text"
    STICKER = "sticker"
    SUBSCRIPTION = "subscription"


class ChatProfile(BaseModel):
    """Chat user profile."""

    model_config = ConfigDict(populate_by_name=True)

    user_id_hash: str | None = Field(default=None, alias="userIdHash")
    nickname: str | None = None
    profile_image_url: str | None = Field(default=None, alias="profileImageUrl")
    user_role_code: str | None = Field(default=None, alias="userRoleCode")
    badge: dict[str, Any] | None = None
    title: dict[str, Any] | None = None
    verified_mark: bool = Field(default=False, alias="verifiedMark")
    activity_badges: list[dict[str, Any]] = Field(default_factory=list, alias="activityBadges")
    streaming_property: dict[str, Any] | None = Field(default=None, alias="streamingProperty")


class ChatMessageExtra(BaseModel):
    """Extra data for chat messages."""

    model_config = ConfigDict(populate_by_name=True)

    chat_type: str | None = Field(default=None, alias="chatType")
    emojis: dict[str, str] | None = None
    os_type: str | None = Field(default=None, alias="osType")
    streaming_channel_id: str | None = Field(default=None, alias="streamingChannelId")


class ChatMessage(BaseModel):
    """Chat message from WebSocket."""

    model_config = ConfigDict(populate_by_name=True)

    service_id: str | None = Field(default=None, alias="svcid")
    channel_id: str | None = Field(default=None, alias="cid")
    message_time: int | None = Field(default=None, alias="msgTime")
    user_id_hash: str | None = Field(default=None, alias="uid")
    profile: ChatProfile | None = None
    content: str | None = Field(default=None, alias="msg")
    message_type_code: int | None = Field(default=None, alias="msgTypeCode")
    message_status_code: str | None = Field(default=None, alias="msgStatusCode")
    extras: ChatMessageExtra | None = None

    @property
    def nickname(self) -> str:
        """Get the user's nickname."""
        if self.profile and self.profile.nickname:
            return self.profile.nickname
        return "Unknown"


class DonationMessage(BaseModel):
    """Donation message from WebSocket."""

    model_config = ConfigDict(populate_by_name=True)

    service_id: str | None = Field(default=None, alias="svcid")
    channel_id: str | None = Field(default=None, alias="cid")
    message_time: int | None = Field(default=None, alias="msgTime")
    user_id_hash: str | None = Field(default=None, alias="uid")
    profile: ChatProfile | None = None
    content: str | None = Field(default=None, alias="msg")
    extras: dict[str, Any] | None = None

    # Donation specific fields
    pay_type: str | None = Field(default=None, alias="payType")
    pay_amount: int = Field(default=0, alias="payAmount")
    donation_type: str | None = Field(default=None, alias="donationType")

    @property
    def nickname(self) -> str:
        """Get the donor's nickname."""
        if self.profile and self.profile.nickname:
            return self.profile.nickname
        return "Unknown"
