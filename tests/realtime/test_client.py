"""Tests for realtime event clients."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from chzzk.exceptions import SessionConnectionError
from chzzk.models.session import (
    ChatEvent,
    DonationEvent,
    DonationType,
    SubscriptionEvent,
    SystemEvent,
    SystemMessageType,
    UserRoleCode,
)
from chzzk.realtime.client import AsyncChzzkEventClient, ChzzkEventClient


class TestChzzkEventClient:
    """Tests for synchronous ChzzkEventClient."""

    @pytest.fixture
    def mock_session_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def client(self, mock_session_service: MagicMock) -> ChzzkEventClient:
        return ChzzkEventClient(mock_session_service)

    def test_initial_state(self, client: ChzzkEventClient) -> None:
        assert client.session_key is None
        assert client.is_connected is False

    def test_on_chat_decorator_registers_handler(
        self,
        client: ChzzkEventClient,
    ) -> None:
        @client.on_chat
        def handle_chat(event: ChatEvent) -> None:
            pass

        assert handle_chat in client._chat_handlers

    def test_on_donation_decorator_registers_handler(
        self,
        client: ChzzkEventClient,
    ) -> None:
        @client.on_donation
        def handle_donation(event: DonationEvent) -> None:
            pass

        assert handle_donation in client._donation_handlers

    def test_on_subscription_decorator_registers_handler(
        self,
        client: ChzzkEventClient,
    ) -> None:
        @client.on_subscription
        def handle_subscription(event: SubscriptionEvent) -> None:
            pass

        assert handle_subscription in client._subscription_handlers

    def test_on_system_decorator_registers_handler(
        self,
        client: ChzzkEventClient,
    ) -> None:
        @client.on_system
        def handle_system(event: SystemEvent) -> None:
            pass

        assert handle_system in client._system_handlers

    def test_subscribe_chat_without_connection_raises_error(
        self,
        client: ChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            client.subscribe_chat()

    def test_subscribe_donation_without_connection_raises_error(
        self,
        client: ChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            client.subscribe_donation()

    def test_subscribe_subscription_without_connection_raises_error(
        self,
        client: ChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            client.subscribe_subscription()

    def test_unsubscribe_chat_without_connection_raises_error(
        self,
        client: ChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            client.unsubscribe_chat()

    def test_stop_sets_stop_event(self, client: ChzzkEventClient) -> None:
        client.stop()
        assert client._stop_event.is_set()


class TestAsyncChzzkEventClient:
    """Tests for asynchronous AsyncChzzkEventClient."""

    @pytest.fixture
    def mock_session_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def client(self, mock_session_service: MagicMock) -> AsyncChzzkEventClient:
        return AsyncChzzkEventClient(mock_session_service)

    def test_initial_state(self, client: AsyncChzzkEventClient) -> None:
        assert client.session_key is None
        assert client.is_connected is False

    def test_on_chat_decorator_registers_handler(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        @client.on_chat
        async def handle_chat(event: ChatEvent) -> None:
            pass

        assert handle_chat in client._chat_handlers

    def test_on_donation_decorator_registers_handler(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        @client.on_donation
        async def handle_donation(event: DonationEvent) -> None:
            pass

        assert handle_donation in client._donation_handlers

    def test_on_subscription_decorator_registers_handler(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        @client.on_subscription
        async def handle_subscription(event: SubscriptionEvent) -> None:
            pass

        assert handle_subscription in client._subscription_handlers

    def test_on_system_decorator_registers_handler(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        @client.on_system
        async def handle_system(event: SystemEvent) -> None:
            pass

        assert handle_system in client._system_handlers

    async def test_subscribe_chat_without_connection_raises_error(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            await client.subscribe_chat()

    async def test_subscribe_donation_without_connection_raises_error(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            await client.subscribe_donation()

    async def test_subscribe_subscription_without_connection_raises_error(
        self,
        client: AsyncChzzkEventClient,
    ) -> None:
        with pytest.raises(SessionConnectionError, match="Not connected to session"):
            await client.subscribe_subscription()

    def test_stop_sets_stop_flag(self, client: AsyncChzzkEventClient) -> None:
        client.stop()
        assert client._stop_requested is True


class TestSessionModels:
    """Tests for session model parsing."""

    def test_chat_event_parsing(self) -> None:
        data = {
            "channelId": "channel_123",
            "senderChannelId": "sender_456",
            "profile": {
                "nickname": "TestUser",
                "badges": [],
                "verifiedMark": False,
            },
            "content": "Hello, world!",
            "emojis": {"smile": "https://example.com/smile.png"},
            "messageTime": 1704067200000,
            "userRoleCode": "common_user",
        }

        event = ChatEvent.model_validate(data)

        assert event.channel_id == "channel_123"
        assert event.sender_channel_id == "sender_456"
        assert event.profile.nickname == "TestUser"
        assert event.content == "Hello, world!"
        assert event.emojis == {"smile": "https://example.com/smile.png"}
        assert event.message_time == 1704067200000
        assert event.user_role_code == UserRoleCode.COMMON_USER

    def test_donation_event_parsing(self) -> None:
        data = {
            "channelId": "channel_123",
            "donationType": "CHAT",
            "donatorChannelId": "donator_789",
            "donatorNickname": "GenerosDonator",
            "payAmount": "10000",
            "donationText": "Keep up the great work!",
            "emojis": {},
        }

        event = DonationEvent.model_validate(data)

        assert event.channel_id == "channel_123"
        assert event.donation_type == DonationType.CHAT
        assert event.donator_channel_id == "donator_789"
        assert event.donator_nickname == "GenerosDonator"
        assert event.pay_amount == "10000"
        assert event.donation_text == "Keep up the great work!"

    def test_subscription_event_parsing(self) -> None:
        data = {
            "channelId": "channel_123",
            "subscriberChannelId": "subscriber_111",
            "subscriberNickname": "LoyalFan",
            "month": 12,
            "tierNo": 1,
            "tierName": "Basic Tier",
        }

        event = SubscriptionEvent.model_validate(data)

        assert event.channel_id == "channel_123"
        assert event.subscriber_channel_id == "subscriber_111"
        assert event.subscriber_nickname == "LoyalFan"
        assert event.month == 12
        assert event.tier_no == 1
        assert event.tier_name == "Basic Tier"

    def test_system_event_connected_parsing(self) -> None:
        data = {
            "type": "connected",
            "data": {
                "sessionKey": "session_key_abc",
            },
        }

        event = SystemEvent.model_validate(data)

        assert event.type == SystemMessageType.CONNECTED
        assert event.data is not None
        assert event.data.session_key == "session_key_abc"

    def test_system_event_subscribed_parsing(self) -> None:
        data = {
            "type": "subscribed",
            "data": {
                "eventType": "CHAT",
                "channelId": "channel_123",
            },
        }

        event = SystemEvent.model_validate(data)

        assert event.type == SystemMessageType.SUBSCRIBED
        assert event.data is not None
        assert event.data.event_type is not None
        assert event.data.channel_id == "channel_123"

    def test_system_event_unsubscribed_parsing(self) -> None:
        data = {
            "type": "unsubscribed",
            "data": {
                "eventType": "DONATION",
                "channelId": "channel_456",
            },
        }

        event = SystemEvent.model_validate(data)

        assert event.type == SystemMessageType.UNSUBSCRIBED

    def test_system_event_revoked_parsing(self) -> None:
        data = {
            "type": "revoked",
            "data": {
                "eventType": "SUBSCRIPTION",
                "channelId": "channel_789",
            },
        }

        event = SystemEvent.model_validate(data)

        assert event.type == SystemMessageType.REVOKED
