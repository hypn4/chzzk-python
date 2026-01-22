"""Chat API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.http import CHAT_NOTICE_URL, CHAT_SEND_URL, CHAT_SETTINGS_URL
from chzzk.models.chat import (
    ChatAvailableCondition,
    ChatAvailableGroup,
    ChatMessageResponse,
    ChatSettings,
    UpdateChatSettingsRequest,
)


class ChatService(BaseService):
    """Synchronous Chat API service.

    Provides access to chat-related API endpoints.
    """

    def send_message(self, message: str) -> ChatMessageResponse:
        """Send a chat message.

        Args:
            message: The message to send.

        Returns:
            ChatMessageResponse containing the message ID.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.post(
            CHAT_SEND_URL,
            json={"message": message},
            headers=self._get_token_headers(),
        )
        return ChatMessageResponse.model_validate(data)

    def register_notice(
        self,
        *,
        message: str | None = None,
        message_id: str | None = None,
    ) -> None:
        """Register a chat notice.

        Either message or message_id must be provided.

        Args:
            message: The notice message content.
            message_id: The message ID to use as notice.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
            ValueError: If neither message nor message_id is provided.
        """
        if message is None and message_id is None:
            msg = "Either message or message_id must be provided"
            raise ValueError(msg)

        payload: dict[str, str] = {}
        if message is not None:
            payload["message"] = message
        if message_id is not None:
            payload["messageId"] = message_id

        self._http.post(
            CHAT_NOTICE_URL,
            json=payload,
            headers=self._get_token_headers(),
        )

    def get_settings(self) -> ChatSettings:
        """Get chat settings.

        Returns:
            ChatSettings object containing the chat configuration.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(CHAT_SETTINGS_URL, headers=self._get_token_headers())
        return ChatSettings.model_validate(data)

    def update_settings(
        self,
        *,
        chat_available_condition: ChatAvailableCondition | None = None,
        chat_available_group: ChatAvailableGroup | None = None,
        allow_subscriber_in_follower_mode: bool | None = None,
        min_follower_minute: int | None = None,
        chat_emoji_mode: bool | None = None,
        chat_slow_mode_sec: int | None = None,
    ) -> None:
        """Update chat settings.

        Args:
            chat_available_condition: Chat availability condition.
            chat_available_group: Chat availability group.
            allow_subscriber_in_follower_mode: Allow subscribers in follower-only mode.
            min_follower_minute: Minimum follower minutes required.
            chat_emoji_mode: Enable emoji-only mode.
            chat_slow_mode_sec: Slow mode delay in seconds.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        request = UpdateChatSettingsRequest(
            chat_available_condition=chat_available_condition,
            chat_available_group=chat_available_group,
            allow_subscriber_in_follower_mode=allow_subscriber_in_follower_mode,
            min_follower_minute=min_follower_minute,
            chat_emoji_mode=chat_emoji_mode,
            chat_slow_mode_sec=chat_slow_mode_sec,
        )
        self._http.put(
            CHAT_SETTINGS_URL,
            json=request.model_dump(by_alias=True, exclude_none=True),
            headers=self._get_token_headers(),
        )


class AsyncChatService(AsyncBaseService):
    """Asynchronous Chat API service.

    Provides access to chat-related API endpoints.
    """

    async def send_message(self, message: str) -> ChatMessageResponse:
        """Send a chat message.

        Args:
            message: The message to send.

        Returns:
            ChatMessageResponse containing the message ID.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.post(
            CHAT_SEND_URL,
            json={"message": message},
            headers=await self._get_token_headers(),
        )
        return ChatMessageResponse.model_validate(data)

    async def register_notice(
        self,
        *,
        message: str | None = None,
        message_id: str | None = None,
    ) -> None:
        """Register a chat notice.

        Either message or message_id must be provided.

        Args:
            message: The notice message content.
            message_id: The message ID to use as notice.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
            ValueError: If neither message nor message_id is provided.
        """
        if message is None and message_id is None:
            msg = "Either message or message_id must be provided"
            raise ValueError(msg)

        payload: dict[str, str] = {}
        if message is not None:
            payload["message"] = message
        if message_id is not None:
            payload["messageId"] = message_id

        await self._http.post(
            CHAT_NOTICE_URL,
            json=payload,
            headers=await self._get_token_headers(),
        )

    async def get_settings(self) -> ChatSettings:
        """Get chat settings.

        Returns:
            ChatSettings object containing the chat configuration.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(CHAT_SETTINGS_URL, headers=await self._get_token_headers())
        return ChatSettings.model_validate(data)

    async def update_settings(
        self,
        *,
        chat_available_condition: ChatAvailableCondition | None = None,
        chat_available_group: ChatAvailableGroup | None = None,
        allow_subscriber_in_follower_mode: bool | None = None,
        min_follower_minute: int | None = None,
        chat_emoji_mode: bool | None = None,
        chat_slow_mode_sec: int | None = None,
    ) -> None:
        """Update chat settings.

        Args:
            chat_available_condition: Chat availability condition.
            chat_available_group: Chat availability group.
            allow_subscriber_in_follower_mode: Allow subscribers in follower-only mode.
            min_follower_minute: Minimum follower minutes required.
            chat_emoji_mode: Enable emoji-only mode.
            chat_slow_mode_sec: Slow mode delay in seconds.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        request = UpdateChatSettingsRequest(
            chat_available_condition=chat_available_condition,
            chat_available_group=chat_available_group,
            allow_subscriber_in_follower_mode=allow_subscriber_in_follower_mode,
            min_follower_minute=min_follower_minute,
            chat_emoji_mode=chat_emoji_mode,
            chat_slow_mode_sec=chat_slow_mode_sec,
        )
        await self._http.put(
            CHAT_SETTINGS_URL,
            json=request.model_dump(by_alias=True, exclude_none=True),
            headers=await self._get_token_headers(),
        )
