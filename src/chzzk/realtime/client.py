"""Socket.IO client for Chzzk realtime events."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import socketio  # type: ignore[import-untyped]

from chzzk.exceptions import SessionConnectionError
from chzzk.models.session import (
    ChatEvent,
    DonationEvent,
    SubscriptionEvent,
    SystemEvent,
    SystemMessageType,
)

if TYPE_CHECKING:
    from chzzk.api.session import AsyncSessionService, SessionService

# Type aliases for event handlers
ChatHandler = Callable[[ChatEvent], None]
DonationHandler = Callable[[DonationEvent], None]
SubscriptionHandler = Callable[[SubscriptionEvent], None]
SystemHandler = Callable[[SystemEvent], None]

AsyncChatHandler = Callable[[ChatEvent], Any]
AsyncDonationHandler = Callable[[DonationEvent], Any]
AsyncSubscriptionHandler = Callable[[SubscriptionEvent], Any]
AsyncSystemHandler = Callable[[SystemEvent], Any]


def _parse_event_data(data: str | dict[str, Any]) -> dict[str, Any]:
    """Parse event data from string or dict."""
    if isinstance(data, str):
        return json.loads(data)
    return data


class ChzzkEventClient:
    """Synchronous Socket.IO client for receiving Chzzk realtime events.

    This client connects to Chzzk's Socket.IO server and receives realtime events
    such as chat messages, donations, and subscriptions.

    Example:
        >>> from chzzk import ChzzkClient
        >>> client = ChzzkClient(client_id="...", client_secret="...", access_token="...")
        >>> event_client = client.create_event_client()
        >>>
        >>> @event_client.on_chat
        ... def handle_chat(event):
        ...     print(f"{event.profile.nickname}: {event.content}")
        >>>
        >>> event_client.connect()
        >>> event_client.subscribe_chat()
        >>> event_client.run_forever()
    """

    def __init__(self, session_service: SessionService) -> None:
        """Initialize the event client.

        Args:
            session_service: SessionService instance for API calls.
        """
        self._session_service = session_service
        self._sio = socketio.Client(
            reconnection=False,
            logger=False,
            engineio_logger=False,
        )
        self._session_key: str | None = None
        self._connected = threading.Event()
        self._stop_event = threading.Event()

        # Event handlers
        self._chat_handlers: list[ChatHandler] = []
        self._donation_handlers: list[DonationHandler] = []
        self._subscription_handlers: list[SubscriptionHandler] = []
        self._system_handlers: list[SystemHandler] = []

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up Socket.IO event handlers."""

        @self._sio.on("connect")
        def on_connect() -> None:
            pass

        @self._sio.on("disconnect")
        def on_disconnect() -> None:
            self._connected.clear()
            self._session_key = None

        @self._sio.on("SYSTEM")
        def on_system(data: str | dict[str, Any]) -> None:
            event = SystemEvent.model_validate(_parse_event_data(data))

            # Handle connection established
            if event.type == SystemMessageType.CONNECTED and event.data:
                self._session_key = event.data.session_key
                self._connected.set()

            # Call registered handlers
            for handler in self._system_handlers:
                handler(event)

        @self._sio.on("CHAT")
        def on_chat(data: str | dict[str, Any]) -> None:
            event = ChatEvent.model_validate(_parse_event_data(data))
            for handler in self._chat_handlers:
                handler(event)

        @self._sio.on("DONATION")
        def on_donation(data: str | dict[str, Any]) -> None:
            event = DonationEvent.model_validate(_parse_event_data(data))
            for handler in self._donation_handlers:
                handler(event)

        @self._sio.on("SUBSCRIPTION")
        def on_subscription(data: str | dict[str, Any]) -> None:
            event = SubscriptionEvent.model_validate(_parse_event_data(data))
            for handler in self._subscription_handlers:
                handler(event)

    @property
    def session_key(self) -> str | None:
        """Get the current session key."""
        return self._session_key

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected.is_set()

    def connect(self, *, use_client_auth: bool = False, timeout: float = 10.0) -> str:
        """Connect to the Socket.IO server.

        Args:
            use_client_auth: If True, use client authentication instead of user authentication.
            timeout: Connection timeout in seconds.

        Returns:
            The session key for the connection.

        Raises:
            SessionConnectionError: If connection fails or times out.
        """
        # Get session URL from API
        if use_client_auth:
            response = self._session_service.create_client_session()
        else:
            response = self._session_service.create_session()

        try:
            self._sio.connect(
                response.url,
                transports=["websocket"],
            )
        except Exception as e:
            raise SessionConnectionError(f"Failed to connect: {e}") from e

        # Wait for SYSTEM connected message
        if not self._connected.wait(timeout=timeout):
            self._sio.disconnect()
            raise SessionConnectionError("Connection timeout: did not receive session key")

        # After successful wait, session_key is guaranteed to be set by the handler
        assert self._session_key is not None
        return self._session_key

    def disconnect(self) -> None:
        """Disconnect from the Socket.IO server."""
        self._stop_event.set()
        if self._sio.connected:
            self._sio.disconnect()
        self._connected.clear()
        self._session_key = None

    def subscribe_chat(self) -> None:
        """Subscribe to chat events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        self._session_service.subscribe_chat(self._session_key)

    def subscribe_donation(self) -> None:
        """Subscribe to donation events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        self._session_service.subscribe_donation(self._session_key)

    def subscribe_subscription(self) -> None:
        """Subscribe to subscription events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        self._session_service.subscribe_subscription(self._session_key)

    def unsubscribe_chat(self) -> None:
        """Unsubscribe from chat events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        self._session_service.unsubscribe_chat(self._session_key)

    def unsubscribe_donation(self) -> None:
        """Unsubscribe from donation events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        self._session_service.unsubscribe_donation(self._session_key)

    def unsubscribe_subscription(self) -> None:
        """Unsubscribe from subscription events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        self._session_service.unsubscribe_subscription(self._session_key)

    def run_forever(self) -> None:
        """Run the event loop until disconnected or stop() is called."""
        self._stop_event.clear()
        try:
            while self._sio.connected and not self._stop_event.is_set():
                self._sio.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()

    def stop(self) -> None:
        """Signal the event loop to stop."""
        self._stop_event.set()

    # Decorator-based event handler registration

    def on_chat(self, handler: ChatHandler) -> ChatHandler:
        """Decorator to register a chat event handler.

        Args:
            handler: Function to handle chat events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_chat
            ... def handle_chat(event):
            ...     print(f"{event.profile.nickname}: {event.content}")
        """
        self._chat_handlers.append(handler)
        return handler

    def on_donation(self, handler: DonationHandler) -> DonationHandler:
        """Decorator to register a donation event handler.

        Args:
            handler: Function to handle donation events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_donation
            ... def handle_donation(event):
            ...     print(f"{event.donator_nickname} donated {event.pay_amount}")
        """
        self._donation_handlers.append(handler)
        return handler

    def on_subscription(self, handler: SubscriptionHandler) -> SubscriptionHandler:
        """Decorator to register a subscription event handler.

        Args:
            handler: Function to handle subscription events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_subscription
            ... def handle_subscription(event):
            ...     print(f"{event.subscriber_nickname} subscribed for {event.month} months")
        """
        self._subscription_handlers.append(handler)
        return handler

    def on_system(self, handler: SystemHandler) -> SystemHandler:
        """Decorator to register a system event handler.

        Args:
            handler: Function to handle system events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_system
            ... def handle_system(event):
            ...     print(f"System event: {event.type}")
        """
        self._system_handlers.append(handler)
        return handler


class AsyncChzzkEventClient:
    """Asynchronous Socket.IO client for receiving Chzzk realtime events.

    This client connects to Chzzk's Socket.IO server and receives realtime events
    such as chat messages, donations, and subscriptions.

    Example:
        >>> import asyncio
        >>> from chzzk import AsyncChzzkClient
        >>>
        >>> async def main():
        ...     async with AsyncChzzkClient(...) as client:
        ...         event_client = client.create_event_client()
        ...
        ...         @event_client.on_chat
        ...         async def handle_chat(event):
        ...             print(f"{event.profile.nickname}: {event.content}")
        ...
        ...         await event_client.connect()
        ...         await event_client.subscribe_chat()
        ...         await event_client.run_forever()
        >>>
        >>> asyncio.run(main())
    """

    def __init__(self, session_service: AsyncSessionService) -> None:
        """Initialize the async event client.

        Args:
            session_service: AsyncSessionService instance for API calls.
        """
        self._session_service = session_service
        self._sio = socketio.AsyncClient(
            reconnection=False,
            logger=False,
            engineio_logger=False,
        )
        self._session_key: str | None = None
        self._connected_event: Any = None  # asyncio.Event, set lazily
        self._stop_requested = False

        # Event handlers
        self._chat_handlers: list[AsyncChatHandler] = []
        self._donation_handlers: list[AsyncDonationHandler] = []
        self._subscription_handlers: list[AsyncSubscriptionHandler] = []
        self._system_handlers: list[AsyncSystemHandler] = []

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up Socket.IO event handlers."""

        @self._sio.on("connect")
        async def on_connect() -> None:
            pass

        @self._sio.on("disconnect")
        async def on_disconnect() -> None:
            if self._connected_event:
                self._connected_event.clear()
            self._session_key = None

        @self._sio.on("SYSTEM")
        async def on_system(data: str | dict[str, Any]) -> None:
            event = SystemEvent.model_validate(_parse_event_data(data))

            # Handle connection established
            if event.type == SystemMessageType.CONNECTED and event.data:
                self._session_key = event.data.session_key
                if self._connected_event:
                    self._connected_event.set()

            # Call registered handlers
            for handler in self._system_handlers:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result

        @self._sio.on("CHAT")
        async def on_chat(data: str | dict[str, Any]) -> None:
            event = ChatEvent.model_validate(_parse_event_data(data))
            for handler in self._chat_handlers:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result

        @self._sio.on("DONATION")
        async def on_donation(data: str | dict[str, Any]) -> None:
            event = DonationEvent.model_validate(_parse_event_data(data))
            for handler in self._donation_handlers:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result

        @self._sio.on("SUBSCRIPTION")
        async def on_subscription(data: str | dict[str, Any]) -> None:
            event = SubscriptionEvent.model_validate(_parse_event_data(data))
            for handler in self._subscription_handlers:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result

    @property
    def session_key(self) -> str | None:
        """Get the current session key."""
        return self._session_key

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected_event is not None and self._connected_event.is_set()

    async def connect(self, *, use_client_auth: bool = False, timeout: float = 10.0) -> str:
        """Connect to the Socket.IO server.

        Args:
            use_client_auth: If True, use client authentication instead of user authentication.
            timeout: Connection timeout in seconds.

        Returns:
            The session key for the connection.

        Raises:
            SessionConnectionError: If connection fails or times out.
        """
        import asyncio

        # Create event lazily to ensure we're in an async context
        self._connected_event = asyncio.Event()

        # Get session URL from API
        if use_client_auth:
            response = await self._session_service.create_client_session()
        else:
            response = await self._session_service.create_session()

        try:
            await self._sio.connect(
                response.url,
                transports=["websocket"],
            )
        except Exception as e:
            raise SessionConnectionError(f"Failed to connect: {e}") from e

        # Wait for SYSTEM connected message
        try:
            await asyncio.wait_for(self._connected_event.wait(), timeout=timeout)
        except TimeoutError as e:
            await self._sio.disconnect()
            raise SessionConnectionError("Connection timeout: did not receive session key") from e

        # After successful wait, session_key is guaranteed to be set by the handler
        assert self._session_key is not None
        return self._session_key

    async def disconnect(self) -> None:
        """Disconnect from the Socket.IO server."""
        self._stop_requested = True
        if self._sio.connected:
            await self._sio.disconnect()
        if self._connected_event:
            self._connected_event.clear()
        self._session_key = None

    async def subscribe_chat(self) -> None:
        """Subscribe to chat events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        await self._session_service.subscribe_chat(self._session_key)

    async def subscribe_donation(self) -> None:
        """Subscribe to donation events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        await self._session_service.subscribe_donation(self._session_key)

    async def subscribe_subscription(self) -> None:
        """Subscribe to subscription events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        await self._session_service.subscribe_subscription(self._session_key)

    async def unsubscribe_chat(self) -> None:
        """Unsubscribe from chat events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        await self._session_service.unsubscribe_chat(self._session_key)

    async def unsubscribe_donation(self) -> None:
        """Unsubscribe from donation events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        await self._session_service.unsubscribe_donation(self._session_key)

    async def unsubscribe_subscription(self) -> None:
        """Unsubscribe from subscription events for this session.

        Raises:
            SessionConnectionError: If not connected.
        """
        if not self._session_key:
            raise SessionConnectionError("Not connected to session")
        await self._session_service.unsubscribe_subscription(self._session_key)

    async def run_forever(self) -> None:
        """Run the event loop until disconnected or stop() is called."""
        import asyncio

        self._stop_requested = False
        try:
            while self._sio.connected and not self._stop_requested:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.disconnect()

    def stop(self) -> None:
        """Signal the event loop to stop."""
        self._stop_requested = True

    # Decorator-based event handler registration

    def on_chat(self, handler: AsyncChatHandler) -> AsyncChatHandler:
        """Decorator to register a chat event handler.

        Args:
            handler: Async function to handle chat events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_chat
            ... async def handle_chat(event):
            ...     print(f"{event.profile.nickname}: {event.content}")
        """
        self._chat_handlers.append(handler)
        return handler

    def on_donation(self, handler: AsyncDonationHandler) -> AsyncDonationHandler:
        """Decorator to register a donation event handler.

        Args:
            handler: Async function to handle donation events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_donation
            ... async def handle_donation(event):
            ...     print(f"{event.donator_nickname} donated {event.pay_amount}")
        """
        self._donation_handlers.append(handler)
        return handler

    def on_subscription(self, handler: AsyncSubscriptionHandler) -> AsyncSubscriptionHandler:
        """Decorator to register a subscription event handler.

        Args:
            handler: Async function to handle subscription events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_subscription
            ... async def handle_subscription(event):
            ...     print(f"{event.subscriber_nickname} subscribed for {event.month} months")
        """
        self._subscription_handlers.append(handler)
        return handler

    def on_system(self, handler: AsyncSystemHandler) -> AsyncSystemHandler:
        """Decorator to register a system event handler.

        Args:
            handler: Async function to handle system events.

        Returns:
            The handler function (unchanged).

        Example:
            >>> @event_client.on_system
            ... async def handle_system(event):
            ...     print(f"System event: {event.type}")
        """
        self._system_handlers.append(handler)
        return handler
