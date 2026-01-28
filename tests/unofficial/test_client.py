"""Tests for the unofficial chat client module."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from chzzk.unofficial.chat.client import AsyncUnofficialChatClient, UnofficialChatClient


class TestUnofficialChatClient:
    """Tests for the synchronous UnofficialChatClient."""

    def test_initialization_with_cookies(self) -> None:
        """Test client initialization with cookies."""
        client = UnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses")

        assert client._auth.get_cookies()["NID_AUT"] == "test_aut"
        assert client._auth.get_cookies()["NID_SES"] == "test_ses"
        assert client.is_connected is False
        assert client.chat_channel_id is None

    def test_initialization_with_auto_reconnect_config(self) -> None:
        """Test client initialization with custom auto-reconnect configuration."""
        client = UnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
            auto_reconnect=True,
            poll_interval=5.0,
            max_reconnect_attempts=10,
            reconnect_backoff_base=2.0,
            reconnect_backoff_max=60.0,
        )

        assert client._auto_reconnect is True
        assert client._monitor_config.poll_interval_seconds == 5.0
        assert client._monitor_config.max_reconnect_attempts == 10
        assert client._monitor_config.reconnect_backoff_base == 2.0
        assert client._monitor_config.reconnect_backoff_max == 60.0

    def test_event_handler_registration(self) -> None:
        """Test event handler registration methods."""
        client = UnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses")

        @client.on_chat
        def chat_handler(msg):
            pass

        @client.on_donation
        def donation_handler(msg):
            pass

        @client.on_system
        def system_handler(data):
            pass

        @client.on_live
        def live_handler(event):
            pass

        @client.on_offline
        def offline_handler(event):
            pass

        @client.on_reconnect
        def reconnect_handler(event):
            pass

        @client.on_reconnect_error
        def reconnect_error_handler(error):
            pass

        assert chat_handler in client._chat_handlers
        assert donation_handler in client._donation_handlers
        assert system_handler in client._system_handlers
        assert live_handler in client._live_handlers
        assert offline_handler in client._offline_handlers
        assert reconnect_handler in client._reconnect_handlers
        assert reconnect_error_handler in client._reconnect_error_handlers

    def test_context_manager(self) -> None:
        """Test client as context manager."""
        with UnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses") as client:
            assert isinstance(client, UnofficialChatClient)

    def test_websocket_thread_wait_on_reconnect(self) -> None:
        """Test that WebSocket thread is waited for during reconnection."""
        client = UnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses")

        # Set up mock WebSocket and thread
        mock_ws = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True

        client._ws = mock_ws
        client._ws_thread = mock_thread

        # Make the reconnection fail after the first attempt (after closing the ws)
        # This allows us to test the thread.join was called

        # First call returns False (continue loop), subsequent calls return True
        call_count = [0]

        def side_effect():
            call_count[0] += 1
            return call_count[0] > 1

        client._stop_event = Mock()
        client._stop_event.is_set.side_effect = side_effect
        client._stop_event.wait = Mock()  # Don't actually wait

        # Mock the chat service to fail
        client._chat_service = Mock()
        client._chat_service.get_access_token.side_effect = Exception("Mock error")

        # Call _perform_reconnection
        client._perform_reconnection("old_chat", "new_chat")

        # Verify thread.join was called
        mock_thread.join.assert_called_with(timeout=5.0)


class TestAsyncUnofficialChatClient:
    """Tests for the asynchronous AsyncUnofficialChatClient."""

    def test_initialization_with_cookies(self) -> None:
        """Test async client initialization with cookies."""
        client = AsyncUnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses")

        assert client._auth.get_cookies()["NID_AUT"] == "test_aut"
        assert client._auth.get_cookies()["NID_SES"] == "test_ses"
        assert client.is_connected is False
        assert client.chat_channel_id is None

    def test_initialization_with_reconnect_wait_timeout(self) -> None:
        """Test async client initialization with reconnect_wait_timeout."""
        client = AsyncUnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
            reconnect_wait_timeout=60.0,
        )

        assert client._reconnect_wait_timeout == 60.0

    def test_initialization_with_infinite_wait(self) -> None:
        """Test async client initialization with infinite wait (None timeout)."""
        client = AsyncUnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
            reconnect_wait_timeout=None,  # Infinite wait
        )

        assert client._reconnect_wait_timeout is None

    def test_initialization_with_auto_reconnect_config(self) -> None:
        """Test async client initialization with custom auto-reconnect configuration."""
        client = AsyncUnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
            auto_reconnect=True,
            poll_interval=5.0,
            max_reconnect_attempts=10,
            reconnect_backoff_base=2.0,
            reconnect_backoff_max=60.0,
            reconnect_wait_timeout=120.0,
        )

        assert client._auto_reconnect is True
        assert client._monitor_config.poll_interval_seconds == 5.0
        assert client._monitor_config.max_reconnect_attempts == 10
        assert client._monitor_config.reconnect_backoff_base == 2.0
        assert client._monitor_config.reconnect_backoff_max == 60.0
        assert client._reconnect_wait_timeout == 120.0

    def test_event_handler_registration(self) -> None:
        """Test event handler registration methods."""
        client = AsyncUnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses")

        @client.on_chat
        async def chat_handler(msg):
            pass

        @client.on_donation
        async def donation_handler(msg):
            pass

        @client.on_system
        async def system_handler(data):
            pass

        @client.on_live
        async def live_handler(event):
            pass

        @client.on_offline
        async def offline_handler(event):
            pass

        @client.on_reconnect
        async def reconnect_handler(event):
            pass

        @client.on_reconnect_error
        async def reconnect_error_handler(error):
            pass

        assert chat_handler in client._chat_handlers
        assert donation_handler in client._donation_handlers
        assert system_handler in client._system_handlers
        assert live_handler in client._live_handlers
        assert offline_handler in client._offline_handlers
        assert reconnect_handler in client._reconnect_handlers
        assert reconnect_error_handler in client._reconnect_error_handlers

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test async client as context manager."""
        async with AsyncUnofficialChatClient(nid_aut="test_aut", nid_ses="test_ses") as client:
            assert isinstance(client, AsyncUnofficialChatClient)


class TestReconnectWaitTimeout:
    """Tests for the reconnect_wait_timeout option."""

    def test_reconnect_wait_timeout_stored(self) -> None:
        """Test that reconnect_wait_timeout is properly stored."""
        client = AsyncUnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
            reconnect_wait_timeout=60.0,
        )
        assert client._reconnect_wait_timeout == 60.0

    def test_reconnect_wait_timeout_none_means_infinite(self) -> None:
        """Test that None timeout means infinite wait."""
        client = AsyncUnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
            reconnect_wait_timeout=None,
        )
        assert client._reconnect_wait_timeout is None

    def test_reconnect_wait_timeout_default_is_none(self) -> None:
        """Test that default timeout is None (infinite wait)."""
        client = AsyncUnofficialChatClient(
            nid_aut="test_aut",
            nid_ses="test_ses",
        )
        assert client._reconnect_wait_timeout is None
