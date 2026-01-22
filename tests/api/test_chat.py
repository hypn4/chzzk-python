"""Tests for Chat API service."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.chat import AsyncChatService, ChatService
from chzzk.http import CHAT_NOTICE_URL, CHAT_SEND_URL, CHAT_SETTINGS_URL
from chzzk.http.client import AsyncHTTPClient, HTTPClient
from chzzk.models import ChatAvailableCondition, ChatAvailableGroup


class TestChatService:
    """Tests for synchronous ChatService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> ChatService:
        return ChatService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_send_message_success(
        self,
        service: ChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_SEND_URL,
            method="POST",
            json={
                "code": 200,
                "content": {
                    "messageId": "msg_12345",
                },
            },
        )

        response = service.send_message("Hello, world!")

        assert response.message_id == "msg_12345"

    def test_register_notice_with_message(
        self,
        service: ChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_NOTICE_URL,
            method="POST",
            status_code=204,
        )

        service.register_notice(message="This is a notice")

        request = httpx_mock.get_request()
        assert request is not None

    def test_register_notice_with_message_id(
        self,
        service: ChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_NOTICE_URL,
            method="POST",
            status_code=204,
        )

        service.register_notice(message_id="msg_12345")

        request = httpx_mock.get_request()
        assert request is not None

    def test_register_notice_requires_message_or_id(
        self,
        service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="Either message or message_id must be provided"):
            service.register_notice()

    def test_get_settings_success(
        self,
        service: ChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_SETTINGS_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "chatAvailableCondition": "NONE",
                    "chatAvailableGroup": "ALL",
                    "allowSubscriberInFollowerMode": True,
                    "minFollowerMinute": 10,
                    "chatEmojiMode": False,
                    "chatSlowModeSec": 0,
                },
            },
        )

        settings = service.get_settings()

        assert settings.chat_available_condition == ChatAvailableCondition.NONE
        assert settings.chat_available_group == ChatAvailableGroup.ALL
        assert settings.allow_subscriber_in_follower_mode is True
        assert settings.min_follower_minute == 10
        assert settings.chat_emoji_mode is False
        assert settings.chat_slow_mode_sec == 0

    def test_update_settings_success(
        self,
        service: ChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_SETTINGS_URL,
            method="PUT",
            status_code=204,
        )

        service.update_settings(
            chat_available_group=ChatAvailableGroup.FOLLOWER,
            chat_slow_mode_sec=5,
        )

        request = httpx_mock.get_request()
        assert request is not None


class TestAsyncChatService:
    """Tests for asynchronous AsyncChatService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncChatService:
        return AsyncChatService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    async def test_send_message_success(
        self,
        service: AsyncChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_SEND_URL,
            method="POST",
            json={
                "code": 200,
                "content": {
                    "messageId": "async_msg_12345",
                },
            },
        )

        response = await service.send_message("Async hello!")

        assert response.message_id == "async_msg_12345"

    async def test_get_settings_success(
        self,
        service: AsyncChatService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHAT_SETTINGS_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "chatAvailableCondition": "REAL_NAME",
                    "chatAvailableGroup": "SUBSCRIBER",
                    "allowSubscriberInFollowerMode": False,
                    "minFollowerMinute": 0,
                    "chatEmojiMode": True,
                    "chatSlowModeSec": 10,
                },
            },
        )

        settings = await service.get_settings()

        assert settings.chat_available_condition == ChatAvailableCondition.REAL_NAME
        assert settings.chat_available_group == ChatAvailableGroup.SUBSCRIBER
