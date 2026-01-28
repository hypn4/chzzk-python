"""Unified client for unofficial Chzzk API."""

from __future__ import annotations

from chzzk.unofficial.api.chat import AsyncChatTokenService, ChatTokenService
from chzzk.unofficial.api.live import AsyncLiveDetailService, LiveDetailService
from chzzk.unofficial.auth.cookie import CookieStorage, NaverCookieAuth
from chzzk.unofficial.chat.client import AsyncUnofficialChatClient, UnofficialChatClient
from chzzk.unofficial.http.client import AsyncUnofficialHTTPClient, UnofficialHTTPClient


class UnofficialChzzkClient:
    """Synchronous unofficial Chzzk API client.

    Provides access to unofficial Chzzk APIs using Naver cookie authentication.
    This includes live detail information and chat functionality.

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

    def __init__(
        self,
        nid_aut: str | None = None,
        nid_ses: str | None = None,
        *,
        cookie_storage: CookieStorage | None = None,
    ) -> None:
        """Initialize the unofficial Chzzk client.

        Args:
            nid_aut: NID_AUT cookie value from Naver login.
            nid_ses: NID_SES cookie value from Naver login.
            cookie_storage: Optional cookie storage for persistence.
        """
        self._auth = NaverCookieAuth(
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            storage=cookie_storage,
        )
        self._http = UnofficialHTTPClient(auth=self._auth)
        self._init_services()

    def _init_services(self) -> None:
        """Initialize all API services."""
        self._live = LiveDetailService(self._http)
        self._chat_token = ChatTokenService(self._http)

    @property
    def auth(self) -> NaverCookieAuth:
        """Get the authentication instance."""
        return self._auth

    @property
    def live(self) -> LiveDetailService:
        """Get the live detail service."""
        return self._live

    @property
    def chat_token(self) -> ChatTokenService:
        """Get the chat token service."""
        return self._chat_token

    @property
    def is_authenticated(self) -> bool:
        """Check if the client has valid cookies."""
        return self._auth.is_authenticated()

    def create_chat_client(
        self,
        *,
        auto_reconnect: bool = True,
        poll_interval: float = 10.0,
        max_reconnect_attempts: int = 5,
        reconnect_backoff_base: float = 1.0,
        reconnect_backoff_max: float = 30.0,
    ) -> UnofficialChatClient:
        """Create a chat client for WebSocket chat.

        Args:
            auto_reconnect: Enable automatic reconnection on stream restart.
            poll_interval: Interval for polling live status in seconds.
            max_reconnect_attempts: Maximum reconnection attempts.
            reconnect_backoff_base: Base delay for exponential backoff.
            reconnect_backoff_max: Maximum backoff delay.

        Returns:
            UnofficialChatClient instance.

        Example:
            >>> chat = client.create_chat_client()
            >>> @chat.on_chat
            ... def handle_chat(msg):
            ...     print(f"{msg.nickname}: {msg.content}")
            >>> chat.connect("channel-id")
            >>> chat.run_forever()
        """
        return UnofficialChatClient(
            auth=self._auth,
            auto_reconnect=auto_reconnect,
            poll_interval=poll_interval,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_backoff_base=reconnect_backoff_base,
            reconnect_backoff_max=reconnect_backoff_max,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> UnofficialChzzkClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncUnofficialChzzkClient:
    """Asynchronous unofficial Chzzk API client.

    Provides access to unofficial Chzzk APIs using Naver cookie authentication.

    Example:
        >>> import asyncio
        >>> from chzzk.unofficial import AsyncUnofficialChzzkClient
        >>>
        >>> async def main():
        ...     async with AsyncUnofficialChzzkClient(
        ...         nid_aut="your-nid-aut-cookie",
        ...         nid_ses="your-nid-ses-cookie",
        ...     ) as client:
        ...         # Get live detail
        ...         live = await client.live.get_live_detail("channel-id-here")
        ...         print(f"Chat Channel ID: {live.chat_channel_id}")
        ...
        ...         # Create chat client
        ...         chat = client.create_chat_client()
        ...
        ...         @chat.on_chat
        ...         async def handle_chat(msg):
        ...             print(f"{msg.nickname}: {msg.content}")
        ...
        ...         await chat.connect("channel-id-here")
        ...         await chat.run_forever()
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        nid_aut: str | None = None,
        nid_ses: str | None = None,
        *,
        cookie_storage: CookieStorage | None = None,
    ) -> None:
        """Initialize the async unofficial Chzzk client.

        Args:
            nid_aut: NID_AUT cookie value from Naver login.
            nid_ses: NID_SES cookie value from Naver login.
            cookie_storage: Optional cookie storage for persistence.
        """
        self._auth = NaverCookieAuth(
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            storage=cookie_storage,
        )
        self._http = AsyncUnofficialHTTPClient(auth=self._auth)
        self._init_services()

    def _init_services(self) -> None:
        """Initialize all API services."""
        self._live = AsyncLiveDetailService(self._http)
        self._chat_token = AsyncChatTokenService(self._http)

    @property
    def auth(self) -> NaverCookieAuth:
        """Get the authentication instance."""
        return self._auth

    @property
    def live(self) -> AsyncLiveDetailService:
        """Get the live detail service."""
        return self._live

    @property
    def chat_token(self) -> AsyncChatTokenService:
        """Get the chat token service."""
        return self._chat_token

    @property
    def is_authenticated(self) -> bool:
        """Check if the client has valid cookies."""
        return self._auth.is_authenticated()

    def create_chat_client(
        self,
        *,
        auto_reconnect: bool = True,
        poll_interval: float = 10.0,
        max_reconnect_attempts: int = 5,
        reconnect_backoff_base: float = 1.0,
        reconnect_backoff_max: float = 30.0,
        reconnect_wait_timeout: float | None = None,
    ) -> AsyncUnofficialChatClient:
        """Create an async chat client for WebSocket chat.

        Args:
            auto_reconnect: Enable automatic reconnection on stream restart.
            poll_interval: Interval for polling live status in seconds.
            max_reconnect_attempts: Maximum reconnection attempts.
            reconnect_backoff_base: Base delay for exponential backoff.
            reconnect_backoff_max: Maximum backoff delay.
            reconnect_wait_timeout: Timeout for waiting for reconnection.
                None means wait indefinitely.

        Returns:
            AsyncUnofficialChatClient instance.

        Example:
            >>> chat = client.create_chat_client()
            >>> @chat.on_chat
            ... async def handle_chat(msg):
            ...     print(f"{msg.nickname}: {msg.content}")
            >>> await chat.connect("channel-id")
            >>> await chat.run_forever()
        """
        return AsyncUnofficialChatClient(
            auth=self._auth,
            auto_reconnect=auto_reconnect,
            poll_interval=poll_interval,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_backoff_base=reconnect_backoff_base,
            reconnect_backoff_max=reconnect_backoff_max,
            reconnect_wait_timeout=reconnect_wait_timeout,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.close()

    async def __aenter__(self) -> AsyncUnofficialChzzkClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
