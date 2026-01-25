"""Reconnect event models for unofficial Chzzk API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from chzzk.unofficial.models.live import LiveStatus


class ReconnectReason(StrEnum):
    """Reason for chat reconnection."""

    CHAT_CHANNEL_CHANGED = "chat_channel_changed"
    BROADCAST_STARTED = "broadcast_started"
    STREAM_RESTARTED = "stream_restarted"
    CONNECTION_LOST = "connection_lost"


class ReconnectEvent(BaseModel):
    """Event data for chat reconnection.

    Attributes:
        reason: The reason for reconnection.
        old_chat_channel_id: The previous chat channel ID.
        new_chat_channel_id: The new chat channel ID.
        attempt: The reconnection attempt number (1-based).
    """

    reason: ReconnectReason
    old_chat_channel_id: str | None = None
    new_chat_channel_id: str | None = None
    attempt: int = 1


class StatusChangeEvent(BaseModel):
    """Event data for live status change.

    Attributes:
        previous_status: The previous live status.
        current_status: The current live status.
        chat_channel_id: The current chat channel ID.
        live_id: The current live ID.
        live_title: The current live title.
    """

    previous_status: LiveStatus | None = None
    current_status: LiveStatus | None = None
    chat_channel_id: str | None = None
    live_id: int | None = None
    live_title: str | None = None
