"""Status monitor for chat auto-reconnection."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from chzzk.exceptions import ChzzkError
from chzzk.unofficial.models.live import LiveStatus, LiveStatusPolling
from chzzk.unofficial.models.reconnect import ReconnectEvent, StatusChangeEvent

if TYPE_CHECKING:
    from chzzk.unofficial.api.live import AsyncLiveStatusPollingService, LiveStatusPollingService

logger = logging.getLogger(__name__)

# Default configuration constants
DEFAULT_POLL_INTERVAL_SECONDS: float = 10.0
DEFAULT_MAX_RECONNECT_ATTEMPTS: int = 5
DEFAULT_RECONNECT_BACKOFF_BASE: float = 1.0
DEFAULT_RECONNECT_BACKOFF_MAX: float = 30.0


@dataclass
class MonitorConfig:
    """Configuration for status monitoring.

    Attributes:
        enabled: Whether status monitoring is enabled.
        poll_interval_seconds: Interval between status polls.
        auto_reconnect: Whether to automatically reconnect on status changes.
        max_reconnect_attempts: Maximum reconnection attempts before giving up.
        reconnect_backoff_base: Base time for exponential backoff.
        reconnect_backoff_max: Maximum backoff time.
    """

    enabled: bool = True
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    auto_reconnect: bool = True
    max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS
    reconnect_backoff_base: float = DEFAULT_RECONNECT_BACKOFF_BASE
    reconnect_backoff_max: float = DEFAULT_RECONNECT_BACKOFF_MAX


# Type aliases for callbacks
StatusChangeCallback = Callable[[StatusChangeEvent], None]
ReconnectCallback = Callable[[ReconnectEvent], None]
ChatChannelChangeCallback = Callable[[str, str], None]


@dataclass
class StatusMonitorState:
    """Internal state for status monitor."""

    last_status: LiveStatusPolling | None = None
    reconnect_attempt: int = 0
    _callbacks: dict[str, list[Callable[..., Any]]] = field(default_factory=dict)

    def add_callback(self, event_type: str, callback: Callable[..., Any]) -> None:
        """Add a callback for an event type."""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    def get_callbacks(self, event_type: str) -> list[Callable[..., Any]]:
        """Get callbacks for an event type."""
        return self._callbacks.get(event_type, [])


class StatusMonitor:
    """Synchronous status monitor for chat auto-reconnection.

    This monitor polls the live status endpoint in a background thread
    and triggers reconnection when chatChannelId changes.
    """

    def __init__(
        self,
        polling_service: LiveStatusPollingService,
        channel_id: str,
        config: MonitorConfig | None = None,
    ) -> None:
        """Initialize the status monitor.

        Args:
            polling_service: Service for polling live status.
            channel_id: Channel ID to monitor.
            config: Monitor configuration.
        """
        self._polling_service = polling_service
        self._channel_id = channel_id
        self._config = config or MonitorConfig()
        self._state = StatusMonitorState()

        self._monitor_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

        # Callbacks
        self._on_live_callbacks: list[StatusChangeCallback] = []
        self._on_offline_callbacks: list[StatusChangeCallback] = []
        self._on_chat_channel_change_callbacks: list[ChatChannelChangeCallback] = []

    @property
    def is_running(self) -> bool:
        """Check if the monitor is running."""
        return self._running

    @property
    def last_status(self) -> LiveStatusPolling | None:
        """Get the last polled status."""
        return self._state.last_status

    def on_live(self, callback: StatusChangeCallback) -> StatusChangeCallback:
        """Register callback for when broadcast starts."""
        self._on_live_callbacks.append(callback)
        return callback

    def on_offline(self, callback: StatusChangeCallback) -> StatusChangeCallback:
        """Register callback for when broadcast ends."""
        self._on_offline_callbacks.append(callback)
        return callback

    def on_chat_channel_change(
        self, callback: ChatChannelChangeCallback
    ) -> ChatChannelChangeCallback:
        """Register callback for when chatChannelId changes."""
        self._on_chat_channel_change_callbacks.append(callback)
        return callback

    def start(self) -> None:
        """Start the status monitor in a background thread."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"StatusMonitor-{self._channel_id}",
        )
        self._monitor_thread.start()
        logger.debug("Status monitor started for channel %s", self._channel_id)

    def stop(self) -> None:
        """Stop the status monitor."""
        if not self._running:
            return

        self._stop_event.set()
        self._running = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)

        logger.debug("Status monitor stopped for channel %s", self._channel_id)

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                new_status = self._polling_service.get_live_status(self._channel_id)
                self._check_status_changes(self._state.last_status, new_status)
                self._state.last_status = new_status
            except (ChzzkError, OSError) as e:
                logger.warning("Failed to poll live status: %s", e)

            # Wait for the poll interval or until stopped
            self._stop_event.wait(timeout=self._config.poll_interval_seconds)

    def _check_status_changes(self, old: LiveStatusPolling | None, new: LiveStatusPolling) -> None:
        """Check for status changes and trigger callbacks.

        Args:
            old: Previous status (None on first poll).
            new: New status.
        """
        if old is None:
            # First poll, no changes to report
            return

        old_status = old.status
        new_status = new.status
        old_chat_channel_id = old.chat_channel_id
        new_chat_channel_id = new.chat_channel_id

        # Check for live status change
        if old_status != new_status:
            event = StatusChangeEvent(
                previous_status=old_status,
                current_status=new_status,
                chat_channel_id=new_chat_channel_id,
                live_id=new.live_id,
                live_title=new.live_title,
            )

            if new_status == LiveStatus.OPEN:
                for callback in self._on_live_callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error("Error in on_live callback: %s", e)
            elif new_status == LiveStatus.CLOSE:
                for callback in self._on_offline_callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error("Error in on_offline callback: %s", e)

        # Check for chat channel ID change
        if (
            old_chat_channel_id
            and new_chat_channel_id
            and old_chat_channel_id != new_chat_channel_id
        ):
            logger.info(
                "Chat channel ID changed: %s -> %s",
                old_chat_channel_id,
                new_chat_channel_id,
            )
            for change_callback in self._on_chat_channel_change_callbacks:
                try:
                    change_callback(old_chat_channel_id, new_chat_channel_id)
                except Exception as e:
                    logger.error("Error in on_chat_channel_change callback: %s", e)


class AsyncStatusMonitor:
    """Asynchronous status monitor for chat auto-reconnection.

    This monitor polls the live status endpoint using asyncio
    and triggers reconnection when chatChannelId changes.
    """

    def __init__(
        self,
        polling_service: AsyncLiveStatusPollingService,
        channel_id: str,
        config: MonitorConfig | None = None,
    ) -> None:
        """Initialize the async status monitor.

        Args:
            polling_service: Async service for polling live status.
            channel_id: Channel ID to monitor.
            config: Monitor configuration.
        """
        self._polling_service = polling_service
        self._channel_id = channel_id
        self._config = config or MonitorConfig()
        self._state = StatusMonitorState()

        self._monitor_task: asyncio.Task[None] | None = None
        self._stop_requested = False
        self._running = False

        # Callbacks (can be sync or async)
        self._on_live_callbacks: list[Callable[[StatusChangeEvent], Any]] = []
        self._on_offline_callbacks: list[Callable[[StatusChangeEvent], Any]] = []
        self._on_chat_channel_change_callbacks: list[Callable[[str, str], Any]] = []

    @property
    def is_running(self) -> bool:
        """Check if the monitor is running."""
        return self._running

    @property
    def last_status(self) -> LiveStatusPolling | None:
        """Get the last polled status."""
        return self._state.last_status

    def on_live(
        self, callback: Callable[[StatusChangeEvent], Any]
    ) -> Callable[[StatusChangeEvent], Any]:
        """Register callback for when broadcast starts."""
        self._on_live_callbacks.append(callback)
        return callback

    def on_offline(
        self, callback: Callable[[StatusChangeEvent], Any]
    ) -> Callable[[StatusChangeEvent], Any]:
        """Register callback for when broadcast ends."""
        self._on_offline_callbacks.append(callback)
        return callback

    def on_chat_channel_change(
        self, callback: Callable[[str, str], Any]
    ) -> Callable[[str, str], Any]:
        """Register callback for when chatChannelId changes."""
        self._on_chat_channel_change_callbacks.append(callback)
        return callback

    def start(self) -> None:
        """Start the status monitor as an asyncio task."""
        if self._running:
            return

        self._stop_requested = False
        self._running = True

        self._monitor_task = asyncio.create_task(
            self._monitor_loop(),
            name=f"AsyncStatusMonitor-{self._channel_id}",
        )
        logger.debug("Async status monitor started for channel %s", self._channel_id)

    async def stop(self) -> None:
        """Stop the status monitor."""
        if not self._running:
            return

        self._stop_requested = True
        self._running = False

        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task

        logger.debug("Async status monitor stopped for channel %s", self._channel_id)

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_requested:
            try:
                new_status = await self._polling_service.get_live_status(self._channel_id)
                await self._check_status_changes(self._state.last_status, new_status)
                self._state.last_status = new_status
            except asyncio.CancelledError:
                break
            except (ChzzkError, OSError) as e:
                logger.warning("Failed to poll live status: %s", e)

            try:
                await asyncio.sleep(self._config.poll_interval_seconds)
            except asyncio.CancelledError:
                break

    async def _check_status_changes(
        self, old: LiveStatusPolling | None, new: LiveStatusPolling
    ) -> None:
        """Check for status changes and trigger callbacks.

        Args:
            old: Previous status (None on first poll).
            new: New status.
        """
        if old is None:
            return

        old_status = old.status
        new_status = new.status
        old_chat_channel_id = old.chat_channel_id
        new_chat_channel_id = new.chat_channel_id

        # Check for live status change
        if old_status != new_status:
            event = StatusChangeEvent(
                previous_status=old_status,
                current_status=new_status,
                chat_channel_id=new_chat_channel_id,
                live_id=new.live_id,
                live_title=new.live_title,
            )

            if new_status == LiveStatus.OPEN:
                for callback in self._on_live_callbacks:
                    try:
                        result = callback(event)
                        if hasattr(result, "__await__"):
                            await result
                    except Exception as e:
                        logger.error("Error in on_live callback: %s", e)
            elif new_status == LiveStatus.CLOSE:
                for callback in self._on_offline_callbacks:
                    try:
                        result = callback(event)
                        if hasattr(result, "__await__"):
                            await result
                    except Exception as e:
                        logger.error("Error in on_offline callback: %s", e)

        # Check for chat channel ID change
        if (
            old_chat_channel_id
            and new_chat_channel_id
            and old_chat_channel_id != new_chat_channel_id
        ):
            logger.info(
                "Chat channel ID changed: %s -> %s",
                old_chat_channel_id,
                new_chat_channel_id,
            )
            for change_callback in self._on_chat_channel_change_callbacks:
                try:
                    result = change_callback(old_chat_channel_id, new_chat_channel_id)
                    if hasattr(result, "__await__"):
                        await result
                except Exception as e:
                    logger.error("Error in on_chat_channel_change callback: %s", e)


def calculate_backoff(attempt: int, base: float, max_backoff: float) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (1-based).
        base: Base delay in seconds.
        max_backoff: Maximum delay in seconds.

    Returns:
        Delay in seconds.
    """
    delay = base * (2 ** (attempt - 1))
    return min(delay, max_backoff)
