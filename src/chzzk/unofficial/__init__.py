"""Unofficial Chzzk API module.

This module provides access to unofficial Chzzk APIs using Naver cookie authentication.
It includes live detail information and WebSocket chat functionality.

Example:
    >>> from chzzk.unofficial import UnofficialChzzkClient
    >>>
    >>> client = UnofficialChzzkClient(
    ...     nid_aut="your-nid-aut-cookie",
    ...     nid_ses="your-nid-ses-cookie",
    ... )
    >>>
    >>> # Get live detail
    >>> live = client.live.get_live_detail("channel-id-here")
    >>> print(f"Chat Channel ID: {live.chat_channel_id}")
    >>>
    >>> # Create chat client
    >>> chat = client.create_chat_client()
    >>>
    >>> @chat.on_chat
    ... def handle_chat(msg):
    ...     print(f"{msg.nickname}: {msg.content}")
    >>>
    >>> chat.connect("channel-id-here")
    >>> chat.run_forever()
"""

from chzzk.unofficial.api import (
    AsyncChatTokenService,
    AsyncLiveDetailService,
    AsyncLiveStatusPollingService,
    AsyncUserStatusService,
    ChatTokenService,
    LiveDetailService,
    LiveStatusPollingService,
    UserStatusService,
)
from chzzk.unofficial.auth import CookieStorage, FileCookieStorage, NaverCookieAuth
from chzzk.unofficial.chat import (
    AsyncUnofficialChatClient,
    ChatHandler,
    UnofficialChatClient,
)
from chzzk.unofficial.client import AsyncUnofficialChzzkClient, UnofficialChzzkClient
from chzzk.unofficial.models import (
    ChatAccessToken,
    ChatCmd,
    ChatMessage,
    ChatMessageExtra,
    ChatProfile,
    ChatType,
    DonationMessage,
    LiveDetail,
    LiveStatus,
    LiveStatusPolling,
    ReconnectEvent,
    ReconnectReason,
    StatusChangeEvent,
    UserStatus,
)

__all__ = [
    # Clients
    "AsyncUnofficialChzzkClient",
    "AsyncUnofficialChatClient",
    "UnofficialChzzkClient",
    "UnofficialChatClient",
    # Services
    "AsyncChatTokenService",
    "AsyncLiveDetailService",
    "AsyncLiveStatusPollingService",
    "AsyncUserStatusService",
    "ChatTokenService",
    "LiveDetailService",
    "LiveStatusPollingService",
    "UserStatusService",
    # Auth
    "CookieStorage",
    "FileCookieStorage",
    "NaverCookieAuth",
    # Chat
    "ChatHandler",
    # Models
    "ChatAccessToken",
    "ChatCmd",
    "ChatMessage",
    "ChatMessageExtra",
    "ChatProfile",
    "ChatType",
    "DonationMessage",
    "LiveDetail",
    "LiveStatus",
    "LiveStatusPolling",
    "ReconnectEvent",
    "ReconnectReason",
    "StatusChangeEvent",
    "UserStatus",
]
