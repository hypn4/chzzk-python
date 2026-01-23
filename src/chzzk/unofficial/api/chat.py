"""Chat token service for unofficial Chzzk API."""

from __future__ import annotations

from chzzk.unofficial.api.base import AsyncUnofficialBaseService, UnofficialBaseService
from chzzk.unofficial.http.endpoints import chat_access_token_url
from chzzk.unofficial.models.chat import ChatAccessToken


class ChatTokenService(UnofficialBaseService):
    """Service for getting chat access tokens.

    This service provides access to the unofficial chat access token API
    required for WebSocket authentication.
    """

    def get_access_token(self, chat_channel_id: str) -> ChatAccessToken:
        """Get chat access token for a chat channel.

        Args:
            chat_channel_id: The chat channel ID (from live detail).

        Returns:
            ChatAccessToken containing accessToken and extraToken.
        """
        url = chat_access_token_url()
        params = {"channelId": chat_channel_id, "chatType": "STREAMING"}
        data = self._http.get(url, params=params)
        return ChatAccessToken.model_validate(data)


class AsyncChatTokenService(AsyncUnofficialBaseService):
    """Async service for getting chat access tokens."""

    async def get_access_token(self, chat_channel_id: str) -> ChatAccessToken:
        """Get chat access token for a chat channel.

        Args:
            chat_channel_id: The chat channel ID (from live detail).

        Returns:
            ChatAccessToken containing accessToken and extraToken.
        """
        url = chat_access_token_url()
        params = {"channelId": chat_channel_id, "chatType": "STREAMING"}
        data = await self._http.get(url, params=params)
        return ChatAccessToken.model_validate(data)
