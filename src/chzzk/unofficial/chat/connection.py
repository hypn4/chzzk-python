"""WebSocket connection manager for unofficial chat."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chzzk.unofficial.models.chat import ChatAccessToken


def get_chat_server_url(server_id: int | None = None) -> str:
    """Get WebSocket server URL.

    Args:
        server_id: Specific server ID (1-5). If None, random server is selected.

    Returns:
        WebSocket server URL.
    """
    if server_id is None:
        server_id = random.randint(1, 5)
    return f"wss://kr-ss{server_id}.chat.naver.com/chat"


def build_connection_url(
    chat_channel_id: str,
    token: ChatAccessToken,
    *,
    server_id: int | None = None,
) -> str:
    """Build complete WebSocket connection URL.

    Args:
        chat_channel_id: Chat channel ID.
        token: Chat access token.
        server_id: Specific server ID (1-5). If None, random server is selected.

    Returns:
        Complete WebSocket URL with query parameters.
    """
    base_url = get_chat_server_url(server_id)
    return base_url
