"""Tests for the status monitor module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from chzzk.unofficial.chat.monitor import (
    AsyncStatusMonitor,
    MonitorConfig,
    StatusMonitor,
    StatusMonitorState,
    calculate_backoff,
)
from chzzk.unofficial.models.live import LiveStatus, LiveStatusPolling


def create_mock_status(
    status: LiveStatus = LiveStatus.OPEN,
    chat_channel_id: str | None = "chat123",
    live_id: int | None = 1,
    live_title: str | None = "Test Stream",
) -> LiveStatusPolling:
    """Create a mock LiveStatusPolling object."""
    return LiveStatusPolling(
        status=status,
        chat_channel_id=chat_channel_id,
        live_id=live_id,
        live_title=live_title,
    )


class TestCalculateBackoff:
    """Tests for the calculate_backoff function."""

    def test_first_attempt(self) -> None:
        """First attempt should use base delay."""
        assert calculate_backoff(1, base=1.0, max_backoff=30.0) == 1.0

    def test_second_attempt(self) -> None:
        """Second attempt should double the delay."""
        assert calculate_backoff(2, base=1.0, max_backoff=30.0) == 2.0

    def test_third_attempt(self) -> None:
        """Third attempt should quadruple the delay."""
        assert calculate_backoff(3, base=1.0, max_backoff=30.0) == 4.0

    def test_respects_max_backoff(self) -> None:
        """Delay should not exceed max_backoff."""
        assert calculate_backoff(10, base=1.0, max_backoff=30.0) == 30.0

    def test_custom_base(self) -> None:
        """Custom base should be used correctly."""
        assert calculate_backoff(1, base=2.0, max_backoff=30.0) == 2.0
        assert calculate_backoff(2, base=2.0, max_backoff=30.0) == 4.0


class TestMonitorConfig:
    """Tests for MonitorConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MonitorConfig()
        assert config.enabled is True
        assert config.poll_interval_seconds == 10.0
        assert config.auto_reconnect is True
        assert config.max_reconnect_attempts == 5
        assert config.reconnect_backoff_base == 1.0
        assert config.reconnect_backoff_max == 30.0
        assert config.max_consecutive_failures == 10
        assert config.infinite_retry is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = MonitorConfig(
            enabled=False,
            poll_interval_seconds=5.0,
            max_consecutive_failures=3,
            infinite_retry=False,
        )
        assert config.enabled is False
        assert config.poll_interval_seconds == 5.0
        assert config.max_consecutive_failures == 3
        assert config.infinite_retry is False


class TestStatusMonitorState:
    """Tests for StatusMonitorState."""

    def test_initial_state(self) -> None:
        """Test initial state values."""
        state = StatusMonitorState()
        assert state.last_status is None
        assert state.reconnect_attempt == 0
        assert state.consecutive_failures == 0

    def test_add_and_get_callbacks(self) -> None:
        """Test callback registration and retrieval."""
        state = StatusMonitorState()
        callback1 = Mock()
        callback2 = Mock()

        state.add_callback("test_event", callback1)
        state.add_callback("test_event", callback2)

        callbacks = state.get_callbacks("test_event")
        assert callback1 in callbacks
        assert callback2 in callbacks

    def test_get_nonexistent_callbacks(self) -> None:
        """Getting callbacks for unregistered event returns empty list."""
        state = StatusMonitorState()
        assert state.get_callbacks("nonexistent") == []


class TestStatusMonitor:
    """Tests for the synchronous StatusMonitor."""

    def test_initial_state(self) -> None:
        """Test monitor initial state."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        assert monitor.is_running is False
        assert monitor.last_status is None

    def test_first_poll_no_change(self) -> None:
        """First poll should not trigger any change callbacks."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        on_live_callback = Mock()
        on_offline_callback = Mock()
        monitor.on_live(on_live_callback)
        monitor.on_offline(on_offline_callback)

        # Simulate first poll
        new_status = create_mock_status(LiveStatus.OPEN)
        monitor._check_status_changes(None, new_status)

        on_live_callback.assert_not_called()
        on_offline_callback.assert_not_called()

    def test_open_to_close_triggers_offline(self) -> None:
        """OPEN to CLOSE transition should trigger on_offline callback."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        on_offline_callback = Mock()
        monitor.on_offline(on_offline_callback)

        old_status = create_mock_status(LiveStatus.OPEN)
        new_status = create_mock_status(LiveStatus.CLOSE, chat_channel_id=None)

        monitor._check_status_changes(old_status, new_status)

        on_offline_callback.assert_called_once()
        event = on_offline_callback.call_args[0][0]
        assert event.previous_status == LiveStatus.OPEN
        assert event.current_status == LiveStatus.CLOSE

    def test_close_to_open_triggers_live(self) -> None:
        """CLOSE to OPEN transition should trigger on_live callback."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        on_live_callback = Mock()
        monitor.on_live(on_live_callback)

        old_status = create_mock_status(LiveStatus.CLOSE, chat_channel_id=None)
        new_status = create_mock_status(LiveStatus.OPEN, chat_channel_id="new_chat123")

        monitor._check_status_changes(old_status, new_status)

        on_live_callback.assert_called_once()
        event = on_live_callback.call_args[0][0]
        assert event.previous_status == LiveStatus.CLOSE
        assert event.current_status == LiveStatus.OPEN

    def test_chat_channel_id_change_during_live(self) -> None:
        """Chat channel ID change during live should trigger callback."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        on_change_callback = Mock()
        monitor.on_chat_channel_change(on_change_callback)

        old_status = create_mock_status(LiveStatus.OPEN, chat_channel_id="old_chat")
        new_status = create_mock_status(LiveStatus.OPEN, chat_channel_id="new_chat")

        monitor._check_status_changes(old_status, new_status)

        on_change_callback.assert_called_once_with("old_chat", "new_chat")

    def test_stream_restart_with_new_chat_channel(self) -> None:
        """Stream restart (CLOSE -> OPEN) with new chat channel ID triggers both callbacks."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        on_live_callback = Mock()
        on_change_callback = Mock()
        monitor.on_live(on_live_callback)
        monitor.on_chat_channel_change(on_change_callback)

        old_status = create_mock_status(LiveStatus.CLOSE, chat_channel_id=None)
        new_status = create_mock_status(LiveStatus.OPEN, chat_channel_id="new_chat")

        monitor._check_status_changes(old_status, new_status)

        on_live_callback.assert_called_once()
        on_change_callback.assert_called_once_with(None, "new_chat")

    def test_on_poll_error_callback(self) -> None:
        """Test on_poll_error callback registration."""
        polling_service = Mock()
        monitor = StatusMonitor(polling_service, "channel123")

        callback = Mock()
        result = monitor.on_poll_error(callback)

        assert result is callback
        assert callback in monitor._on_poll_error_callbacks


class TestAsyncStatusMonitor:
    """Tests for the asynchronous AsyncStatusMonitor."""

    @pytest.mark.asyncio
    async def test_first_poll_no_change(self) -> None:
        """First poll should not trigger any change callbacks."""
        polling_service = AsyncMock()
        monitor = AsyncStatusMonitor(polling_service, "channel123")

        on_live_callback = Mock()
        on_offline_callback = Mock()
        monitor.on_live(on_live_callback)
        monitor.on_offline(on_offline_callback)

        # Simulate first poll
        new_status = create_mock_status(LiveStatus.OPEN)
        await monitor._check_status_changes(None, new_status)

        on_live_callback.assert_not_called()
        on_offline_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_open_to_close_triggers_offline(self) -> None:
        """OPEN to CLOSE transition should trigger on_offline callback."""
        polling_service = AsyncMock()
        monitor = AsyncStatusMonitor(polling_service, "channel123")

        on_offline_callback = Mock()
        monitor.on_offline(on_offline_callback)

        old_status = create_mock_status(LiveStatus.OPEN)
        new_status = create_mock_status(LiveStatus.CLOSE, chat_channel_id=None)

        await monitor._check_status_changes(old_status, new_status)

        on_offline_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_to_open_triggers_live(self) -> None:
        """CLOSE to OPEN transition should trigger on_live callback."""
        polling_service = AsyncMock()
        monitor = AsyncStatusMonitor(polling_service, "channel123")

        on_live_callback = Mock()
        monitor.on_live(on_live_callback)

        old_status = create_mock_status(LiveStatus.CLOSE, chat_channel_id=None)
        new_status = create_mock_status(LiveStatus.OPEN, chat_channel_id="new_chat123")

        await monitor._check_status_changes(old_status, new_status)

        on_live_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_callback_support(self) -> None:
        """Async callbacks should be awaited properly."""
        polling_service = AsyncMock()
        monitor = AsyncStatusMonitor(polling_service, "channel123")

        callback_called = False

        async def async_callback(event):
            nonlocal callback_called
            callback_called = True

        monitor.on_live(async_callback)

        old_status = create_mock_status(LiveStatus.CLOSE, chat_channel_id=None)
        new_status = create_mock_status(LiveStatus.OPEN, chat_channel_id="new_chat123")

        await monitor._check_status_changes(old_status, new_status)

        assert callback_called is True

    @pytest.mark.asyncio
    async def test_on_poll_error_callback(self) -> None:
        """Test on_poll_error callback registration."""
        polling_service = AsyncMock()
        monitor = AsyncStatusMonitor(polling_service, "channel123")

        callback = AsyncMock()
        result = monitor.on_poll_error(callback)

        assert result is callback
        assert callback in monitor._on_poll_error_callbacks


class TestConsecutiveFailures:
    """Tests for consecutive failure handling."""

    def test_sync_monitor_consecutive_failure_counting(self) -> None:
        """Test that consecutive failures are counted correctly."""
        from chzzk.exceptions import ChzzkError

        polling_service = Mock()
        polling_service.get_live_status.side_effect = ChzzkError("Network error")

        config = MonitorConfig(
            poll_interval_seconds=0.01,
            max_consecutive_failures=3,
            infinite_retry=False,
        )
        monitor = StatusMonitor(polling_service, "channel123", config)

        poll_error_callback = Mock()
        monitor.on_poll_error(poll_error_callback)

        # Run the monitor for a short time
        monitor.start()
        import time
        time.sleep(0.1)
        monitor.stop()

        # Callback should have been called when max failures reached
        poll_error_callback.assert_called()
        # First argument should be the failure count
        assert poll_error_callback.call_args[0][0] >= 3

    def test_sync_monitor_stops_when_infinite_retry_false(self) -> None:
        """Monitor should stop when infinite_retry is False and max failures reached."""
        from chzzk.exceptions import ChzzkError

        polling_service = Mock()
        polling_service.get_live_status.side_effect = ChzzkError("Network error")

        config = MonitorConfig(
            poll_interval_seconds=0.01,
            max_consecutive_failures=2,
            infinite_retry=False,
        )
        monitor = StatusMonitor(polling_service, "channel123", config)

        monitor.start()
        import time
        time.sleep(0.1)

        # Monitor should have stopped itself
        assert monitor.is_running is False or not monitor._monitor_thread.is_alive()
        monitor.stop()  # Clean up

    def test_sync_monitor_continues_when_infinite_retry_true(self) -> None:
        """Monitor should continue when infinite_retry is True."""
        from chzzk.exceptions import ChzzkError

        call_count = 0

        def failing_service(*args):
            nonlocal call_count
            call_count += 1
            raise ChzzkError("Network error")

        polling_service = Mock()
        polling_service.get_live_status.side_effect = failing_service

        config = MonitorConfig(
            poll_interval_seconds=0.01,
            max_consecutive_failures=2,
            infinite_retry=True,
        )
        monitor = StatusMonitor(polling_service, "channel123", config)

        monitor.start()
        import time
        time.sleep(0.15)
        monitor.stop()

        # With infinite_retry, it should have made more calls than max_consecutive_failures
        assert call_count > 2

    def test_sync_monitor_resets_on_success(self) -> None:
        """Consecutive failure counter should reset on successful poll."""
        from chzzk.exceptions import ChzzkError

        polling_service = Mock()

        # First call fails, subsequent calls succeed
        call_count = 0

        def mock_get_live_status(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ChzzkError("Network error")
            return create_mock_status()

        polling_service.get_live_status.side_effect = mock_get_live_status

        config = MonitorConfig(
            poll_interval_seconds=0.01,
            max_consecutive_failures=5,
        )
        monitor = StatusMonitor(polling_service, "channel123", config)

        monitor.start()
        import time
        time.sleep(0.1)
        monitor.stop()

        assert monitor._state.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_async_monitor_consecutive_failure_counting(self) -> None:
        """Test async monitor consecutive failure counting."""
        from chzzk.exceptions import ChzzkError

        polling_service = AsyncMock()
        polling_service.get_live_status.side_effect = ChzzkError("Network error")

        config = MonitorConfig(
            poll_interval_seconds=0.01,
            max_consecutive_failures=3,
            infinite_retry=False,
        )
        monitor = AsyncStatusMonitor(polling_service, "channel123", config)

        poll_error_callback = AsyncMock()
        monitor.on_poll_error(poll_error_callback)

        monitor.start()
        await asyncio.sleep(0.1)
        await monitor.stop()

        # Callback should have been called
        poll_error_callback.assert_called()
        assert poll_error_callback.call_args[0][0] >= 3
