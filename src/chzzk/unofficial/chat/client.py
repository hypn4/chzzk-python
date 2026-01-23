"""Chat client for unofficial Chzzk API."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import websocket

from chzzk.constants import WSConfig
from chzzk.exceptions import ChatConnectionError, ChatNotLiveError, ChatReconnectError, ChzzkError
from chzzk.unofficial.api.chat import AsyncChatTokenService, ChatTokenService
from chzzk.unofficial.api.live import (
    AsyncLiveDetailService,
    AsyncLiveStatusPollingService,
    LiveDetailService,
    LiveStatusPollingService,
)
from chzzk.unofficial.api.user import AsyncUserStatusService, UserStatusService
from chzzk.unofficial.auth.cookie import NaverCookieAuth
from chzzk.unofficial.chat.connection import build_connection_url
from chzzk.unofficial.chat.handler import ChatHandler
from chzzk.unofficial.chat.monitor import (
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_RECONNECT_BACKOFF_BASE,
    DEFAULT_RECONNECT_BACKOFF_MAX,
    AsyncStatusMonitor,
    MonitorConfig,
    StatusMonitor,
    calculate_backoff,
)
from chzzk.unofficial.http.client import AsyncUnofficialHTTPClient, UnofficialHTTPClient
from chzzk.unofficial.models.chat import ChatAccessToken, ChatCmd, ChatMessage, DonationMessage
from chzzk.unofficial.models.live import LiveDetail
from chzzk.unofficial.models.reconnect import ReconnectEvent, ReconnectReason, StatusChangeEvent

logger = logging.getLogger(__name__)

# Type aliases for event handlers
ChatMessageHandler = Callable[[ChatMessage], None]
DonationMessageHandler = Callable[[DonationMessage], None]
SystemMessageHandler = Callable[[dict[str, Any]], None]
StatusChangeHandler = Callable[[StatusChangeEvent], None]
ReconnectHandler = Callable[[ReconnectEvent], None]
ReconnectErrorHandler = Callable[[Exception], None]

AsyncChatMessageHandler = Callable[[ChatMessage], Any]
AsyncDonationMessageHandler = Callable[[DonationMessage], Any]
AsyncSystemMessageHandler = Callable[[dict[str, Any]], Any]
AsyncStatusChangeHandler = Callable[[StatusChangeEvent], Any]
AsyncReconnectHandler = Callable[[ReconnectEvent], Any]
AsyncReconnectErrorHandler = Callable[[Exception], Any]


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
        auto_reconnect: bool = True,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        reconnect_backoff_base: float = DEFAULT_RECONNECT_BACKOFF_BASE,
        reconnect_backoff_max: float = DEFAULT_RECONNECT_BACKOFF_MAX,
    ) -> None:
        """Initialize the chat client.

        Args:
            nid_aut: NID_AUT cookie value.
            nid_ses: NID_SES cookie value.
            auth: NaverCookieAuth instance (alternative to nid_aut/nid_ses).
            auto_reconnect: Whether to automatically reconnect when chat channel changes.
            poll_interval: Interval for polling live status (seconds).
            max_reconnect_attempts: Maximum reconnection attempts.
            reconnect_backoff_base: Base delay for exponential backoff (seconds).
            reconnect_backoff_max: Maximum backoff delay (seconds).
        """
        if auth:
            self._auth = auth
        else:
            self._auth = NaverCookieAuth(nid_aut=nid_aut, nid_ses=nid_ses)

        self._http = UnofficialHTTPClient(auth=self._auth)
        self._live_service = LiveDetailService(self._http)
        self._polling_service = LiveStatusPollingService(self._http)
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

        # Auto-reconnect configuration
        self._auto_reconnect = auto_reconnect
        self._monitor_config = MonitorConfig(
            enabled=auto_reconnect,
            poll_interval_seconds=poll_interval,
            auto_reconnect=auto_reconnect,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_backoff_base=reconnect_backoff_base,
            reconnect_backoff_max=reconnect_backoff_max,
        )
        self._monitor: StatusMonitor | None = None
        self._reconnecting = threading.Lock()
        self._reconnect_attempt = 0

        # Event handlers
        self._chat_handlers: list[ChatMessageHandler] = []
        self._donation_handlers: list[DonationMessageHandler] = []
        self._system_handlers: list[SystemMessageHandler] = []
        self._live_handlers: list[StatusChangeHandler] = []
        self._offline_handlers: list[StatusChangeHandler] = []
        self._reconnect_handlers: list[ReconnectHandler] = []
        self._reconnect_error_handlers: list[ReconnectErrorHandler] = []

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

    def connect(
        self, channel_id: str, *, timeout: float = 10.0, allow_offline: bool = False
    ) -> None:
        """Connect to chat for a channel.

        Args:
            channel_id: Channel ID to connect to.
            timeout: Connection timeout in seconds.
            allow_offline: If True, connect even when channel is offline.

        Raises:
            ChatNotLiveError: If the channel is not live and allow_offline is False.
            ChatConnectionError: If connection fails.
        """
        # Store the streaming channel ID (original channel_id)
        self._streaming_channel_id = channel_id

        # Get live detail to get chat channel ID
        self._live_detail = self._live_service.get_live_detail(channel_id)

        if not self._live_detail.is_live and not allow_offline:
            raise ChatNotLiveError(f"Channel {channel_id} is not currently live")

        self._chat_channel_id = self._live_detail.chat_channel_id
        if not self._chat_channel_id:
            if not self._live_detail.is_live:
                raise ChatConnectionError(
                    "Chat channel ID not available for offline channel. "
                    "Authentication (NID_AUT/NID_SES cookies) is required to connect "
                    "to chat when the channel is offline."
                )
            raise ChatConnectionError("No chat channel ID found")

        # Get access token
        self._access_token = self._chat_service.get_access_token(self._chat_channel_id)

        # Get user status for authenticated chat (enables sending messages)
        try:
            user_status = self._user_service.get_user_status()
            if user_status.logged_in:
                self._user_id_hash = user_status.user_id_hash
        except (ChzzkError, OSError) as e:
            logger.debug("Failed to get user status (continuing without auth): %s", e)
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
            kwargs={"ping_interval": WSConfig.PING_INTERVAL, "ping_timeout": WSConfig.PING_TIMEOUT},
            daemon=True,
        )
        self._ws_thread.start()

        # Wait for connection
        if not self._connected.wait(timeout=timeout):
            self.disconnect()
            raise ChatConnectionError("Connection timeout")

        # Start status monitor if auto-reconnect is enabled
        if self._auto_reconnect:
            self._start_monitor()

    def _start_monitor(self) -> None:
        """Start the status monitor for auto-reconnection."""
        if self._monitor:
            self._monitor.stop()

        if not self._streaming_channel_id:
            return

        self._monitor = StatusMonitor(
            self._polling_service,
            self._streaming_channel_id,
            self._monitor_config,
        )

        # Register internal callbacks
        self._monitor.on_live(self._handle_live_status)
        self._monitor.on_offline(self._handle_offline_status)
        self._monitor.on_chat_channel_change(self._handle_chat_channel_change)

        self._monitor.start()

    def _stop_monitor(self) -> None:
        """Stop the status monitor."""
        if self._monitor:
            self._monitor.stop()
            self._monitor = None

    def _handle_live_status(self, event: StatusChangeEvent) -> None:
        """Handle broadcast start event."""
        for handler in self._live_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Error in on_live handler: %s", e)

    def _handle_offline_status(self, event: StatusChangeEvent) -> None:
        """Handle broadcast end event."""
        for handler in self._offline_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Error in on_offline handler: %s", e)

    def _handle_chat_channel_change(self, old_id: str, new_id: str) -> None:
        """Handle chat channel ID change - trigger reconnection."""
        if not self._auto_reconnect:
            return

        # Use a lock to prevent concurrent reconnection attempts
        if not self._reconnecting.acquire(blocking=False):
            return

        try:
            self._perform_reconnection(old_id, new_id)
        finally:
            self._reconnecting.release()

    def _perform_reconnection(self, old_id: str, new_id: str) -> None:
        """Perform the actual reconnection with exponential backoff."""
        self._reconnect_attempt = 0
        max_attempts = self._monitor_config.max_reconnect_attempts

        while self._reconnect_attempt < max_attempts and not self._stop_event.is_set():
            self._reconnect_attempt += 1

            try:
                logger.info(
                    "Reconnecting attempt %d/%d: %s -> %s",
                    self._reconnect_attempt,
                    max_attempts,
                    old_id,
                    new_id,
                )

                # Close existing WebSocket
                if self._ws:
                    self._ws.close()
                    self._ws = None
                self._connected.clear()

                # Update chat channel ID
                self._chat_channel_id = new_id

                # Get new access token
                self._access_token = self._chat_service.get_access_token(new_id)

                # Build new WebSocket URL
                ws_url = build_connection_url(new_id, self._access_token)

                # Create new WebSocket
                self._ws = websocket.WebSocketApp(
                    ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                # Start WebSocket in background thread
                ws_kwargs = {
                    "ping_interval": WSConfig.PING_INTERVAL,
                    "ping_timeout": WSConfig.PING_TIMEOUT,
                }
                self._ws_thread = threading.Thread(
                    target=self._ws.run_forever,
                    kwargs=ws_kwargs,
                    daemon=True,
                )
                self._ws_thread.start()

                # Wait for connection
                if self._connected.wait(timeout=10.0):
                    # Success - notify handlers
                    event = ReconnectEvent(
                        reason=ReconnectReason.CHAT_CHANNEL_CHANGED,
                        old_chat_channel_id=old_id,
                        new_chat_channel_id=new_id,
                        attempt=self._reconnect_attempt,
                    )
                    for handler in self._reconnect_handlers:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error("Error in on_reconnect handler: %s", e)

                    self._reconnect_attempt = 0
                    return

                # Connection timeout, will retry
                logger.warning("Reconnection attempt %d timed out", self._reconnect_attempt)

            except Exception as e:
                logger.warning("Reconnection attempt %d failed: %s", self._reconnect_attempt, e)

            # Calculate backoff delay
            if self._reconnect_attempt < max_attempts:
                delay = calculate_backoff(
                    self._reconnect_attempt,
                    self._monitor_config.reconnect_backoff_base,
                    self._monitor_config.reconnect_backoff_max,
                )
                logger.debug("Waiting %.1f seconds before next attempt", delay)
                time.sleep(delay)

        # All attempts exhausted
        error = ChatReconnectError(
            f"Failed to reconnect after {max_attempts} attempts",
            attempt=self._reconnect_attempt,
            max_attempts=max_attempts,
        )
        for error_handler in self._reconnect_error_handlers:
            try:
                error_handler(error)
            except Exception as e:
                logger.error("Error in on_reconnect_error handler: %s", e)

    def disconnect(self) -> None:
        """Disconnect from chat."""
        self._stop_event.set()
        self._stop_monitor()
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
                    for donation_handler in self._donation_handlers:
                        donation_handler(donation)

            else:
                # Other system messages
                for system_handler in self._system_handlers:
                    system_handler(data)

        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            logger.debug("Failed to parse WebSocket message: %s", e)

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

    def on_live(self, handler: StatusChangeHandler) -> StatusChangeHandler:
        """Decorator to register a broadcast start handler.

        Example:
            >>> @chat.on_live
            ... def handle_live(event):
            ...     print(f"Broadcast started: {event.live_title}")
        """
        self._live_handlers.append(handler)
        return handler

    def on_offline(self, handler: StatusChangeHandler) -> StatusChangeHandler:
        """Decorator to register a broadcast end handler.

        Example:
            >>> @chat.on_offline
            ... def handle_offline(event):
            ...     print("Broadcast ended")
        """
        self._offline_handlers.append(handler)
        return handler

    def on_reconnect(self, handler: ReconnectHandler) -> ReconnectHandler:
        """Decorator to register a reconnection success handler.

        Example:
            >>> @chat.on_reconnect
            ... def handle_reconnect(event):
            ...     print(f"Reconnected: {event.old_chat_channel_id}")
        """
        self._reconnect_handlers.append(handler)
        return handler

    def on_reconnect_error(self, handler: ReconnectErrorHandler) -> ReconnectErrorHandler:
        """Decorator to register a reconnection failure handler.

        Example:
            >>> @chat.on_reconnect_error
            ... def handle_error(error):
            ...     print(f"Reconnection failed: {error}")
        """
        self._reconnect_error_handlers.append(handler)
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
        auto_reconnect: bool = True,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        reconnect_backoff_base: float = DEFAULT_RECONNECT_BACKOFF_BASE,
        reconnect_backoff_max: float = DEFAULT_RECONNECT_BACKOFF_MAX,
    ) -> None:
        """Initialize the async chat client.

        Args:
            nid_aut: NID_AUT cookie value.
            nid_ses: NID_SES cookie value.
            auth: NaverCookieAuth instance (alternative to nid_aut/nid_ses).
            auto_reconnect: Whether to automatically reconnect when chat channel changes.
            poll_interval: Interval for polling live status (seconds).
            max_reconnect_attempts: Maximum reconnection attempts.
            reconnect_backoff_base: Base delay for exponential backoff (seconds).
            reconnect_backoff_max: Maximum backoff delay (seconds).
        """
        if auth:
            self._auth = auth
        else:
            self._auth = NaverCookieAuth(nid_aut=nid_aut, nid_ses=nid_ses)

        self._http = AsyncUnofficialHTTPClient(auth=self._auth)
        self._live_service = AsyncLiveDetailService(self._http)
        self._polling_service = AsyncLiveStatusPollingService(self._http)
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

        # Auto-reconnect configuration
        self._auto_reconnect = auto_reconnect
        self._monitor_config = MonitorConfig(
            enabled=auto_reconnect,
            poll_interval_seconds=poll_interval,
            auto_reconnect=auto_reconnect,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_backoff_base=reconnect_backoff_base,
            reconnect_backoff_max=reconnect_backoff_max,
        )
        self._monitor: AsyncStatusMonitor | None = None
        self._reconnecting = asyncio.Lock()
        self._reconnect_attempt = 0
        self._message_loop_task: asyncio.Task[None] | None = None

        # Event handlers
        self._chat_handlers: list[AsyncChatMessageHandler] = []
        self._donation_handlers: list[AsyncDonationMessageHandler] = []
        self._system_handlers: list[AsyncSystemMessageHandler] = []
        self._live_handlers: list[AsyncStatusChangeHandler] = []
        self._offline_handlers: list[AsyncStatusChangeHandler] = []
        self._reconnect_handlers: list[AsyncReconnectHandler] = []
        self._reconnect_error_handlers: list[AsyncReconnectErrorHandler] = []

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

    async def connect(
        self, channel_id: str, *, timeout: float = 10.0, allow_offline: bool = False
    ) -> None:
        """Connect to chat for a channel.

        Args:
            channel_id: Channel ID to connect to.
            timeout: Connection timeout in seconds.
            allow_offline: If True, connect even when channel is offline.

        Raises:
            ChatNotLiveError: If the channel is not live and allow_offline is False.
            ChatConnectionError: If connection fails.
        """
        import websockets

        # Store the streaming channel ID (original channel_id)
        self._streaming_channel_id = channel_id

        # Get live detail to get chat channel ID
        self._live_detail = await self._live_service.get_live_detail(channel_id)

        if not self._live_detail.is_live and not allow_offline:
            raise ChatNotLiveError(f"Channel {channel_id} is not currently live")

        self._chat_channel_id = self._live_detail.chat_channel_id
        if not self._chat_channel_id:
            if not self._live_detail.is_live:
                raise ChatConnectionError(
                    "Chat channel ID not available for offline channel. "
                    "Authentication (NID_AUT/NID_SES cookies) is required to connect "
                    "to chat when the channel is offline."
                )
            raise ChatConnectionError("No chat channel ID found")

        # Get access token
        self._access_token = await self._chat_service.get_access_token(self._chat_channel_id)

        # Get user status for authenticated chat (enables sending messages)
        try:
            user_status = await self._user_service.get_user_status()
            if user_status.logged_in:
                self._user_id_hash = user_status.user_id_hash
        except (ChzzkError, OSError) as e:
            logger.debug("Failed to get user status (continuing without auth): %s", e)
            self._user_id_hash = None

        # Build WebSocket URL
        ws_url = build_connection_url(self._chat_channel_id, self._access_token)

        try:
            self._ws = await asyncio.wait_for(
                websockets.connect(
                    ws_url,
                    ping_interval=WSConfig.PING_INTERVAL,
                    ping_timeout=WSConfig.PING_TIMEOUT,
                ),
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

        # Start status monitor if auto-reconnect is enabled
        if self._auto_reconnect:
            self._start_monitor()

    def _start_monitor(self) -> None:
        """Start the status monitor for auto-reconnection."""
        if self._monitor:
            self._monitor.stop()

        if not self._streaming_channel_id:
            return

        self._monitor = AsyncStatusMonitor(
            self._polling_service,
            self._streaming_channel_id,
            self._monitor_config,
        )

        # Register internal callbacks
        self._monitor.on_live(self._handle_live_status)
        self._monitor.on_offline(self._handle_offline_status)
        self._monitor.on_chat_channel_change(self._handle_chat_channel_change)

        self._monitor.start()

    def _stop_monitor(self) -> None:
        """Stop the status monitor."""
        if self._monitor:
            self._monitor.stop()
            self._monitor = None

    async def _handle_live_status(self, event: StatusChangeEvent) -> None:
        """Handle broadcast start event."""
        for handler in self._live_handlers:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Error in on_live handler: %s", e)

    async def _handle_offline_status(self, event: StatusChangeEvent) -> None:
        """Handle broadcast end event."""
        for handler in self._offline_handlers:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Error in on_offline handler: %s", e)

    async def _handle_chat_channel_change(self, old_id: str, new_id: str) -> None:
        """Handle chat channel ID change - trigger reconnection."""
        if not self._auto_reconnect:
            return

        async with self._reconnecting:
            await self._perform_reconnection(old_id, new_id)

    async def _perform_reconnection(self, old_id: str, new_id: str) -> None:
        """Perform the actual reconnection with exponential backoff."""
        import websockets

        self._reconnect_attempt = 0
        max_attempts = self._monitor_config.max_reconnect_attempts

        while self._reconnect_attempt < max_attempts and not self._stop_requested:
            self._reconnect_attempt += 1

            try:
                logger.info(
                    "Reconnecting attempt %d/%d: %s -> %s",
                    self._reconnect_attempt,
                    max_attempts,
                    old_id,
                    new_id,
                )

                # Close existing WebSocket
                if self._ws:
                    await self._ws.close()
                    self._ws = None
                self._connected.clear()

                # Update chat channel ID
                self._chat_channel_id = new_id

                # Get new access token
                self._access_token = await self._chat_service.get_access_token(new_id)

                # Build new WebSocket URL
                ws_url = build_connection_url(new_id, self._access_token)

                # Create new WebSocket
                self._ws = await asyncio.wait_for(
                    websockets.connect(
                        ws_url,
                        ping_interval=WSConfig.PING_INTERVAL,
                        ping_timeout=WSConfig.PING_TIMEOUT,
                    ),
                    timeout=10.0,
                )

                # Send connect message
                connect_msg = self._handler.create_connect_message(
                    new_id,
                    self._access_token.access_token,
                    uid=self._user_id_hash,
                )
                await self._ws.send(connect_msg)

                # Wait for CONNECTED response
                try:
                    async with asyncio.timeout(10.0):
                        while True:
                            message = await self._ws.recv()
                            data = self._handler.parse_message(message)
                            cmd = self._handler.get_command(data)

                            if cmd == ChatCmd.CONNECTED:
                                self._connected.set()
                                bdy = data.get("bdy", {})
                                self._session_id = bdy.get("sid")
                                recent_req = self._handler.create_recent_chat_request(new_id)
                                await self._ws.send(recent_req)
                                break
                except TimeoutError:
                    logger.warning("Reconnection attempt %d timed out", self._reconnect_attempt)
                    continue

                # Success - notify handlers
                event = ReconnectEvent(
                    reason=ReconnectReason.CHAT_CHANNEL_CHANGED,
                    old_chat_channel_id=old_id,
                    new_chat_channel_id=new_id,
                    attempt=self._reconnect_attempt,
                )
                for handler in self._reconnect_handlers:
                    try:
                        result = handler(event)
                        if hasattr(result, "__await__"):
                            await result
                    except Exception as e:
                        logger.error("Error in on_reconnect handler: %s", e)

                self._reconnect_attempt = 0
                return

            except Exception as e:
                logger.warning("Reconnection attempt %d failed: %s", self._reconnect_attempt, e)

            # Calculate backoff delay
            if self._reconnect_attempt < max_attempts:
                delay = calculate_backoff(
                    self._reconnect_attempt,
                    self._monitor_config.reconnect_backoff_base,
                    self._monitor_config.reconnect_backoff_max,
                )
                logger.debug("Waiting %.1f seconds before next attempt", delay)
                await asyncio.sleep(delay)

        # All attempts exhausted
        error = ChatReconnectError(
            f"Failed to reconnect after {max_attempts} attempts",
            attempt=self._reconnect_attempt,
            max_attempts=max_attempts,
        )
        for error_handler in self._reconnect_error_handlers:
            try:
                result = error_handler(error)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Error in on_reconnect_error handler: %s", e)

    async def disconnect(self) -> None:
        """Disconnect from chat."""
        self._stop_requested = True
        self._stop_monitor()
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

                try:
                    await self._handle_message(message)
                except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
                    logger.debug("Failed to handle WebSocket message: %s", e)

        except asyncio.CancelledError:
            pass
        except OSError as e:
            # WebSocket connection errors (e.g., connection reset)
            logger.debug("WebSocket connection error: %s", e)
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
                for donation_handler in self._donation_handlers:
                    result = donation_handler(donation)
                    if hasattr(result, "__await__"):
                        await result

        else:
            # Other system messages
            for system_handler in self._system_handlers:
                result = system_handler(data)
                if hasattr(result, "__await__"):
                    await result

    def stop(self) -> None:
        """Signal to stop the event loop."""
        self._stop_requested = True
        if self._ws:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._ws.close())
            except RuntimeError:
                # No running loop - will be closed in disconnect()
                pass

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

    def on_live(self, handler: AsyncStatusChangeHandler) -> AsyncStatusChangeHandler:
        """Decorator to register a broadcast start handler.

        Example:
            >>> @chat.on_live
            ... async def handle_live(event):
            ...     print(f"Broadcast started: {event.live_title}")
        """
        self._live_handlers.append(handler)
        return handler

    def on_offline(self, handler: AsyncStatusChangeHandler) -> AsyncStatusChangeHandler:
        """Decorator to register a broadcast end handler.

        Example:
            >>> @chat.on_offline
            ... async def handle_offline(event):
            ...     print("Broadcast ended")
        """
        self._offline_handlers.append(handler)
        return handler

    def on_reconnect(self, handler: AsyncReconnectHandler) -> AsyncReconnectHandler:
        """Decorator to register a reconnection success handler.

        Example:
            >>> @chat.on_reconnect
            ... async def handle_reconnect(event):
            ...     print(f"Reconnected: {event.old_chat_channel_id}")
        """
        self._reconnect_handlers.append(handler)
        return handler

    def on_reconnect_error(self, handler: AsyncReconnectErrorHandler) -> AsyncReconnectErrorHandler:
        """Decorator to register a reconnection failure handler.

        Example:
            >>> @chat.on_reconnect_error
            ... async def handle_error(error):
            ...     print(f"Reconnection failed: {error}")
        """
        self._reconnect_error_handlers.append(handler)
        return handler

    async def close(self) -> None:
        """Close the client and release resources."""
        await self.disconnect()
        await self._http.close()

    async def __aenter__(self) -> AsyncUnofficialChatClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
