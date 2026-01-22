"""Pydantic models for Session API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    """Event type enumeration for session events."""

    CHAT = "CHAT"
    DONATION = "DONATION"
    SUBSCRIPTION = "SUBSCRIPTION"


class SystemMessageType(StrEnum):
    """System message type enumeration."""

    CONNECTED = "connected"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    REVOKED = "revoked"


class DonationType(StrEnum):
    """Donation type enumeration."""

    CHAT = "CHAT"
    VIDEO = "VIDEO"


class UserRoleCode(StrEnum):
    """User role code enumeration."""

    STREAMER = "streamer"
    COMMON_USER = "common_user"
    STREAMING_CHANNEL_MANAGER = "streaming_channel_manager"
    STREAMING_CHAT_MANAGER = "streaming_chat_manager"


# API Response Models


class SessionAuthResponse(BaseModel):
    """Response model for session creation (auth)."""

    url: str

    model_config = {"populate_by_name": True}


class SubscribedEvent(BaseModel):
    """Subscribed event information."""

    event_type: EventType = Field(alias="eventType")
    channel_id: str = Field(alias="channelId")

    model_config = {"populate_by_name": True}


class SessionInfo(BaseModel):
    """Session information."""

    session_key: str = Field(alias="sessionKey")
    connected_date: datetime = Field(alias="connectedDate")
    disconnected_date: datetime | None = Field(default=None, alias="disconnectedDate")
    subscribed_events: list[SubscribedEvent] = Field(default_factory=list, alias="subscribedEvents")

    model_config = {"populate_by_name": True}


class SessionListResponse(BaseModel):
    """Response model for session list."""

    data: list[SessionInfo]

    model_config = {"populate_by_name": True}


# Socket.IO Event Models


class Badge(BaseModel):
    """Badge information for chat profile."""

    image_url: str | None = Field(default=None, alias="imageUrl")

    model_config = {"populate_by_name": True}


class ChatProfile(BaseModel):
    """Chat message sender profile."""

    nickname: str
    badges: list[Badge] = Field(default_factory=list)
    verified_mark: bool = Field(default=False, alias="verifiedMark")

    model_config = {"populate_by_name": True}


class ChatEvent(BaseModel):
    """Chat event message from Socket.IO."""

    channel_id: str = Field(alias="channelId")
    sender_channel_id: str = Field(alias="senderChannelId")
    profile: ChatProfile
    content: str
    emojis: dict[str, str] = Field(default_factory=dict)
    message_time: int = Field(alias="messageTime")
    user_role_code: UserRoleCode = Field(alias="userRoleCode")

    model_config = {"populate_by_name": True}


class DonationEvent(BaseModel):
    """Donation event message from Socket.IO."""

    channel_id: str = Field(alias="channelId")
    donation_type: DonationType = Field(alias="donationType")
    donator_channel_id: str = Field(alias="donatorChannelId")
    donator_nickname: str = Field(alias="donatorNickname")
    pay_amount: str = Field(alias="payAmount")
    donation_text: str = Field(alias="donationText")
    emojis: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class SubscriptionEvent(BaseModel):
    """Subscription event message from Socket.IO."""

    channel_id: str = Field(alias="channelId")
    subscriber_channel_id: str = Field(alias="subscriberChannelId")
    subscriber_nickname: str = Field(alias="subscriberNickname")
    month: int
    tier_no: int = Field(alias="tierNo")
    tier_name: str = Field(alias="tierName")

    model_config = {"populate_by_name": True}


class SystemEventData(BaseModel):
    """System event data."""

    session_key: str | None = Field(default=None, alias="sessionKey")
    event_type: EventType | None = Field(default=None, alias="eventType")
    channel_id: str | None = Field(default=None, alias="channelId")

    model_config = {"populate_by_name": True}


class SystemEvent(BaseModel):
    """System event message from Socket.IO."""

    type: SystemMessageType
    data: SystemEventData | None = None

    model_config = {"populate_by_name": True}
