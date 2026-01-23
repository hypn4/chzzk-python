"""Chat client for unofficial Chzzk API."""

from __future__ import annotations

import asyncio
import contextlib
import threading
from collections.abc import Callable
from typing import Any

import websocket

from chzzk.exceptions import ChatConnectionError, ChatNotLiveError
from chzzk.unofficial.api.chat import AsyncChatTokenService, ChatTokenService
from chzzk.unofficial.api.live import AsyncLiveDetailService, LiveDetailService
from chzzk.unofficial.api.user import AsyncUserStatusService, UserStatusService
from chzzk.unofficial.auth.cookie import NaverCookieAuth
from chzzk.unofficial.chat.connection import build_connection_url
from chzzk.unofficial.chat.handler import ChatHandler
from chzzk.unofficial.http.client import AsyncUnofficialHTTPClient, UnofficialHTTPClient
from chzzk.unofficial.models.chat import ChatAccessToken, ChatCmd, ChatMessage, DonationMessage
from chzzk.unofficial.models.live import LiveDetail

# Type aliases for event handlers
ChatMessageHandler = Callable[[ChatMessage], None]
DonationMessageHandler = Callable[[DonationMessage], None]
SystemMessageHandler = Callable[[dict[str, Any]], None]

AsyncChatMessageHandler = Callable[[ChatMessage], Any]
AsyncDonationMessageHandler = Callable[[DonationMessage], Any]
AsyncSystemMessageHandler = Callable[[dict[str, Any]], Any]


class UnofficialChatClient:
    """Synchronous WebSocket chat client for unofficial Chzzk API.

    This client connects to Chzzk's unofficial chat WebSocket and
    receives real-time chat messages, donations, and system events.

    Example:
        >>> from chzzk.unofficial import UnofficialChatClient
        >>>
        >>> chat = UnofficialChatClient(
        ...     nid_aut="your-nid-aut-cookie",
        ...     nid_ses="your-nid-ses-cookie",
        ... )
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
        auth: NaverCookieAuth | None = None,
    ) -> None:
        """Initialize the chat client.

        Args:
            nid_aut: NID_AUT cookie value.
            nid_ses: NID_SES cookie value.
            auth: NaverCookieAuth instance (alternative to nid_aut/nid_ses).
        """
        if auth:
            self._auth = auth
        else:
            self._auth = NaverCookieAuth(nid_aut=nid_aut, nid_ses=nid_ses)

        self._http = UnofficialHTTPClient(auth=self._auth)
        self._live_service = LiveDetailService(self._http)
        self._chat_service = ChatTokenService(self._http)
        self._user_service = UserStatusService(self._http)
        self._handler = ChatHandler()

        self._ws: websocket.WebSocketApp | None = None
        self._ws_thread: threading.Thread | None = None
        self._connected = threading.Event()
        self._stop_event = threading.Event()

        self._chat_channel_id: str | None = None
        self._access_token: ChatAccessToken | None = None
        self._live_detail: LiveDetail | None = None
        self._user_id_hash: str | None = None
        self._session_id: str | None = None
        self._streaming_channel_id: str | None = None

        # Event handlers
        self._chat_handlers: list[ChatMessageHandler] = []
        self._donation_handlers: list[DonationMessageHandler] = []
        self._system_handlers: list[SystemMessageHandler] = []

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected.is_set()

    @property
    def live_detail(self) -> LiveDetail | None:
        """Get the current live detail."""
        return self._live_detail

    @property
    def chat_channel_id(self) -> str | None:
        """Get the current chat channel ID."""
        return self._chat_channel_id

    def get_live_detail(self, channel_id: str) -> LiveDetail:
        """Get live detail for a channel.

        Args:
            channel_id: Channel ID.

        Returns:
            LiveDetail object.
        """
        return self._live_service.get_live_detail(channel_id)

    def connect(self, channel_id: str, *, timeout: float = 10.0) -> None:
        """Connect to chat for a channel.

        Args:
            channel_id: Channel ID to connect to.
            timeout: Connection timeout in seconds.

        Raises:
            ChatNotLiveError: If the channel is not live.
            ChatConnectionError: If connection fails.
        """
        # Store the streaming channel ID (original channel_id)
        self._streaming_channel_id = channel_id

        # Get live detail to get chat channel ID
        self._live_detail = self._live_service.get_live_detail(channel_id)

        if not self._live_detail.is_live:
            raise ChatNotLiveError(f"Channel {channel_id} is not currently live")

        self._chat_channel_id = self._live_detail.chat_channel_id
        if not self._chat_channel_id:
            raise ChatConnectionError("No chat channel ID found")

        # Get access token
        self._access_token = self._chat_service.get_access_token(self._chat_channel_id)

        # Get user status for authenticated chat (enables sending messages)
        try:
            user_status = self._user_service.get_user_status()
            if user_status.logged_in:
                self._user_id_hash = user_status.user_id_hash
        except Exception:
            self._user_id_hash = None

        # Build WebSocket URL
        ws_url = build_connection_url(self._chat_channel_id, self._access_token)

        # Set up WebSocket
        self._ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        # Start WebSocket in background thread
        self._stop_event.clear()
        self._ws_thread = threading.Thread(
            target=self._ws.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
        )
        self._ws_thread.start()

        # Wait for connection
        if not self._connected.wait(timeout=timeout):
            self.disconnect()
            raise ChatConnectionError("Connection timeout")

    def disconnect(self) -> None:
        """Disconnect from chat."""
        self._stop_event.set()
        if self._ws:
            self._ws.close()
            self._ws = None
        self._connected.clear()
        self._chat_channel_id = None
        self._access_token = None
        self._session_id = None
        self._streaming_channel_id = None

    def send_message(self, content: str) -> None:
        """Send a chat message.

        Args:
            content: Message content.

        Raises:
            ChatConnectionError: If not connected or missing required tokens.
        """
        if not self._ws or not self._chat_channel_id or not self._session_id:
            raise ChatConnectionError("Not connected to chat")
        if not self._access_token:
            raise ChatConnectionError("No access token available")
        if not self._streaming_channel_id:
            raise ChatConnectionError("No streaming channel ID available")

        message = self._handler.create_send_chat_message(
            self._chat_channel_id,
            content,
            session_id=self._session_id,
            extra_token=self._access_token.extra_token,
            streaming_channel_id=self._streaming_channel_id,
        )
        self._ws.send(message)

    def run_forever(self) -> None:
        """Run the event loop until disconnected."""
        try:
            while self._ws_thread and self._ws_thread.is_alive() and not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()

    def stop(self) -> None:
        """Signal to stop the event loop."""
        self._stop_event.set()

    # WebSocket callbacks

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket open."""
        if self._chat_channel_id and self._access_token:
            connect_msg = self._handler.create_connect_message(
                self._chat_channel_id,
                self._access_token.access_token,
                uid=self._user_id_hash,
            )
            ws.send(connect_msg)

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = self._handler.parse_message(message)
            cmd = self._handler.get_command(data)

            if cmd == ChatCmd.CONNECTED:
                self._connected.set()
                # Extract session ID from response
                bdy = data.get("bdy", {})
                self._session_id = bdy.get("sid")
                # Request recent chat
                if self._chat_channel_id:
                    recent_req = self._handler.create_recent_chat_request(self._chat_channel_id)
                    ws.send(recent_req)

            elif cmd == ChatCmd.PING:
                pong = self._handler.create_pong_message()
                ws.send(pong)

            elif cmd in (ChatCmd.CHAT, ChatCmd.RECENT_CHAT):
                messages = self._handler.parse_chat_messages(data)
                for msg in messages:
                    for handler in self._chat_handlers:
                        handler(msg)

            elif cmd == ChatCmd.DONATION:
                donations = self._handler.parse_donation_messages(data)
                for donation in donations:
                    for handler in self._donation_handlers:
                        handler(donation)

            else:
                # Other system messages
                for handler in self._system_handlers:
                    handler(data)

        except Exception:
            # Ignore parsing errors
            pass

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Handle WebSocket error."""
        pass

    def _on_close(
        self, ws: websocket.WebSocketApp, close_status_code: int | None, close_msg: str | None
    ) -> None:
        """Handle WebSocket close."""
        self._connected.clear()

    # Event handler decorators

    def on_chat(self, handler: ChatMessageHandler) -> ChatMessageHandler:
        """Decorator to register a chat message handler.

        Example:
            >>> @chat.on_chat
            ... def handle_chat(msg):
            ...     print(f"{msg.nickname}: {msg.content}")
        """
        self._chat_handlers.append(handler)
        return handler

    def on_donation(self, handler: DonationMessageHandler) -> DonationMessageHandler:
        """Decorator to register a donation message handler.

        Example:
            >>> @chat.on_donation
            ... def handle_donation(msg):
            ...     print(f"{msg.nickname} donated {msg.pay_amount}")
        """
        self._donation_handlers.append(handler)
        return handler

    def on_system(self, handler: SystemMessageHandler) -> SystemMessageHandler:
        """Decorator to register a system message handler.

        Example:
            >>> @chat.on_system
            ... def handle_system(data):
            ...     print(f"System: {data}")
        """
        self._system_handlers.append(handler)
        return handler

    def close(self) -> None:
        """Close the client and release resources."""
        self.disconnect()
        self._http.close()

    def __enter__(self) -> UnofficialChatClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncUnofficialChatClient:
    """Asynchronous WebSocket chat client for unofficial Chzzk API.

    Example:
        >>> import asyncio
        >>> from chzzk.unofficial import AsyncUnofficialChatClient
        >>>
        >>> async def main():
        ...     async with AsyncUnofficialChatClient(
        ...         nid_aut="your-nid-aut-cookie",
        ...         nid_ses="your-nid-ses-cookie",
        ...     ) as chat:
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
        auth: NaverCookieAuth | None = None,
    ) -> None:
        """Initialize the async chat client.

        Args:
            nid_aut: NID_AUT cookie value.
            nid_ses: NID_SES cookie value.
            auth: NaverCookieAuth instance (alternative to nid_aut/nid_ses).
        """
        if auth:
            self._auth = auth
        else:
            self._auth = NaverCookieAuth(nid_aut=nid_aut, nid_ses=nid_ses)

        self._http = AsyncUnofficialHTTPClient(auth=self._auth)
        self._live_service = AsyncLiveDetailService(self._http)
        self._chat_service = AsyncChatTokenService(self._http)
        self._user_service = AsyncUserStatusService(self._http)
        self._handler = ChatHandler()

        self._ws: Any = None  # websockets connection
        self._connected = asyncio.Event()
        self._stop_requested = False

        self._chat_channel_id: str | None = None
        self._access_token: ChatAccessToken | None = None
        self._live_detail: LiveDetail | None = None
        self._user_id_hash: str | None = None
        self._session_id: str | None = None
        self._streaming_channel_id: str | None = None

        # Event handlers
        self._chat_handlers: list[AsyncChatMessageHandler] = []
        self._donation_handlers: list[AsyncDonationMessageHandler] = []
        self._system_handlers: list[AsyncSystemMessageHandler] = []

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected.is_set()

    @property
    def live_detail(self) -> LiveDetail | None:
        """Get the current live detail."""
        return self._live_detail

    @property
    def chat_channel_id(self) -> str | None:
        """Get the current chat channel ID."""
        return self._chat_channel_id

    async def get_live_detail(self, channel_id: str) -> LiveDetail:
        """Get live detail for a channel.

        Args:
            channel_id: Channel ID.

        Returns:
            LiveDetail object.
        """
        return await self._live_service.get_live_detail(channel_id)

    async def connect(self, channel_id: str, *, timeout: float = 10.0) -> None:
        """Connect to chat for a channel.

        Args:
            channel_id: Channel ID to connect to.
            timeout: Connection timeout in seconds.

        Raises:
            ChatNotLiveError: If the channel is not live.
            ChatConnectionError: If connection fails.
        """
        import websockets

        # Store the streaming channel ID (original channel_id)
        self._streaming_channel_id = channel_id

        # Get live detail to get chat channel ID
        self._live_detail = await self._live_service.get_live_detail(channel_id)

        if not self._live_detail.is_live:
            raise ChatNotLiveError(f"Channel {channel_id} is not currently live")

        self._chat_channel_id = self._live_detail.chat_channel_id
        if not self._chat_channel_id:
            raise ChatConnectionError("No chat channel ID found")

        # Get access token
        self._access_token = await self._chat_service.get_access_token(self._chat_channel_id)

        # Get user status for authenticated chat (enables sending messages)
        try:
            user_status = await self._user_service.get_user_status()
            if user_status.logged_in:
                self._user_id_hash = user_status.user_id_hash
        except Exception:
            self._user_id_hash = None

        # Build WebSocket URL
        ws_url = build_connection_url(self._chat_channel_id, self._access_token)

        try:
            self._ws = await asyncio.wait_for(
                websockets.connect(ws_url, ping_interval=20, ping_timeout=10),
                timeout=timeout,
            )
        except TimeoutError as e:
            raise ChatConnectionError("Connection timeout") from e
        except Exception as e:
            raise ChatConnectionError(f"Failed to connect: {e}") from e

        # Send connect message
        connect_msg = self._handler.create_connect_message(
            self._chat_channel_id,
            self._access_token.access_token,
            uid=self._user_id_hash,
        )
        await self._ws.send(connect_msg)

        # Wait for CONNECTED response
        try:
            async with asyncio.timeout(timeout):
                while True:
                    message = await self._ws.recv()
                    data = self._handler.parse_message(message)
                    cmd = self._handler.get_command(data)

                    if cmd == ChatCmd.CONNECTED:
                        self._connected.set()
                        # Extract session ID from response
                        bdy = data.get("bdy", {})
                        self._session_id = bdy.get("sid")
                        # Request recent chat
                        recent_req = self._handler.create_recent_chat_request(self._chat_channel_id)
                        await self._ws.send(recent_req)
                        break
        except TimeoutError as e:
            await self.disconnect()
            raise ChatConnectionError("Connection timeout waiting for CONNECTED") from e

    async def disconnect(self) -> None:
        """Disconnect from chat."""
        self._stop_requested = True
        if self._ws:
            await self._ws.close()
            self._ws = None
        self._connected.clear()
        self._chat_channel_id = None
        self._access_token = None
        self._session_id = None
        self._streaming_channel_id = None

    async def send_message(self, content: str) -> None:
        """Send a chat message.

        Args:
            content: Message content.

        Raises:
            ChatConnectionError: If not connected or missing required tokens.
        """
        if not self._ws or not self._chat_channel_id or not self._session_id:
            raise ChatConnectionError("Not connected to chat")
        if not self._access_token:
            raise ChatConnectionError("No access token available")
        if not self._streaming_channel_id:
            raise ChatConnectionError("No streaming channel ID available")

        message = self._handler.create_send_chat_message(
            self._chat_channel_id,
            content,
            session_id=self._session_id,
            extra_token=self._access_token.extra_token,
            streaming_channel_id=self._streaming_channel_id,
        )
        await self._ws.send(message)

    async def run_forever(self) -> None:
        """Run the event loop until disconnected."""
        if not self._ws:
            raise ChatConnectionError("Not connected to chat")

        self._stop_requested = False

        try:
            async for message in self._ws:
                if self._stop_requested:
                    break

                with contextlib.suppress(Exception):
                    await self._handle_message(message)

        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            await self.disconnect()

    async def _handle_message(self, message: str | bytes) -> None:
        """Handle incoming WebSocket message."""
        data = self._handler.parse_message(message)
        cmd = self._handler.get_command(data)

        if cmd == ChatCmd.PING:
            pong = self._handler.create_pong_message()
            await self._ws.send(pong)

        elif cmd in (ChatCmd.CHAT, ChatCmd.RECENT_CHAT):
            messages = self._handler.parse_chat_messages(data)
            for msg in messages:
                for handler in self._chat_handlers:
                    result = handler(msg)
                    if hasattr(result, "__await__"):
                        await result

        elif cmd == ChatCmd.DONATION:
            donations = self._handler.parse_donation_messages(data)
            for donation in donations:
                for handler in self._donation_handlers:
                    result = handler(donation)
                    if hasattr(result, "__await__"):
                        await result

        else:
            # Other system messages
            for handler in self._system_handlers:
                result = handler(data)
                if hasattr(result, "__await__"):
                    await result

    def stop(self) -> None:
        """Signal to stop the event loop."""
        self._stop_requested = True

    # Event handler decorators

    def on_chat(self, handler: AsyncChatMessageHandler) -> AsyncChatMessageHandler:
        """Decorator to register a chat message handler.

        Example:
            >>> @chat.on_chat
            ... async def handle_chat(msg):
            ...     print(f"{msg.nickname}: {msg.content}")
        """
        self._chat_handlers.append(handler)
        return handler

    def on_donation(self, handler: AsyncDonationMessageHandler) -> AsyncDonationMessageHandler:
        """Decorator to register a donation message handler.

        Example:
            >>> @chat.on_donation
            ... async def handle_donation(msg):
            ...     print(f"{msg.nickname} donated {msg.pay_amount}")
        """
        self._donation_handlers.append(handler)
        return handler

    def on_system(self, handler: AsyncSystemMessageHandler) -> AsyncSystemMessageHandler:
        """Decorator to register a system message handler.

        Example:
            >>> @chat.on_system
            ... async def handle_system(data):
            ...     print(f"System: {data}")
        """
        self._system_handlers.append(handler)
        return handler

    async def close(self) -> None:
        """Close the client and release resources."""
        await self.disconnect()
        await self._http.close()

    async def __aenter__(self) -> AsyncUnofficialChatClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
