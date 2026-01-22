"""Tests for Session API service."""

from __future__ import annotations

import re

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.session import AsyncSessionService, SessionService
from chzzk.http import (
    SESSIONS_AUTH_CLIENT_URL,
    SESSIONS_AUTH_URL,
    SESSIONS_CLIENT_URL,
    SESSIONS_SUBSCRIBE_CHAT_URL,
    SESSIONS_SUBSCRIBE_DONATION_URL,
    SESSIONS_SUBSCRIBE_SUBSCRIPTION_URL,
    SESSIONS_UNSUBSCRIBE_CHAT_URL,
    SESSIONS_UNSUBSCRIBE_DONATION_URL,
    SESSIONS_UNSUBSCRIBE_SUBSCRIPTION_URL,
    SESSIONS_URL,
)
from chzzk.http.client import AsyncHTTPClient, HTTPClient
from chzzk.models import EventType


class TestSessionService:
    """Tests for synchronous SessionService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> SessionService:
        return SessionService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_create_session_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=SESSIONS_AUTH_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "url": "https://ssio08.nchat.naver.com:443?auth=TOKEN",
                },
            },
        )

        response = service.create_session()

        assert response.url == "https://ssio08.nchat.naver.com:443?auth=TOKEN"

    def test_create_client_session_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=SESSIONS_AUTH_CLIENT_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "url": "https://ssio08.nchat.naver.com:443?auth=CLIENT_TOKEN",
                },
            },
        )

        response = service.create_client_session()

        assert response.url == "https://ssio08.nchat.naver.com:443?auth=CLIENT_TOKEN"

    def test_get_sessions_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_URL)}\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "sessionKey": "session_key_1",
                            "connectedDate": "2024-01-01T00:00:00Z",
                            "disconnectedDate": None,
                            "subscribedEvents": [
                                {"eventType": "CHAT", "channelId": "channel_1"},
                            ],
                        },
                        {
                            "sessionKey": "session_key_2",
                            "connectedDate": "2024-01-02T00:00:00Z",
                            "disconnectedDate": "2024-01-02T01:00:00Z",
                            "subscribedEvents": [],
                        },
                    ],
                },
            },
        )

        sessions = service.get_sessions(size=10, page=0)

        assert len(sessions) == 2
        assert sessions[0].session_key == "session_key_1"
        assert sessions[0].disconnected_date is None
        assert len(sessions[0].subscribed_events) == 1
        assert sessions[0].subscribed_events[0].event_type == EventType.CHAT
        assert sessions[0].subscribed_events[0].channel_id == "channel_1"
        assert sessions[1].session_key == "session_key_2"
        assert sessions[1].disconnected_date is not None

    def test_get_client_sessions_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_CLIENT_URL)}\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "sessionKey": "client_session_key",
                            "connectedDate": "2024-01-01T00:00:00Z",
                            "disconnectedDate": None,
                            "subscribedEvents": [],
                        },
                    ],
                },
            },
        )

        sessions = service.get_client_sessions()

        assert len(sessions) == 1
        assert sessions[0].session_key == "client_session_key"

    def test_subscribe_chat_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_SUBSCRIBE_CHAT_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        service.subscribe_chat("test_session_key")

        request = httpx_mock.get_request()
        assert request is not None
        assert "sessionKey=test_session_key" in str(request.url)

    def test_subscribe_donation_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_SUBSCRIBE_DONATION_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        service.subscribe_donation("test_session_key")

        request = httpx_mock.get_request()
        assert request is not None

    def test_subscribe_subscription_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_SUBSCRIBE_SUBSCRIPTION_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        service.subscribe_subscription("test_session_key")

        request = httpx_mock.get_request()
        assert request is not None

    def test_unsubscribe_chat_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_UNSUBSCRIBE_CHAT_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        service.unsubscribe_chat("test_session_key")

        request = httpx_mock.get_request()
        assert request is not None

    def test_unsubscribe_donation_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_UNSUBSCRIBE_DONATION_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        service.unsubscribe_donation("test_session_key")

        request = httpx_mock.get_request()
        assert request is not None

    def test_unsubscribe_subscription_success(
        self,
        service: SessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_UNSUBSCRIBE_SUBSCRIPTION_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        service.unsubscribe_subscription("test_session_key")

        request = httpx_mock.get_request()
        assert request is not None


class TestAsyncSessionService:
    """Tests for asynchronous AsyncSessionService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncSessionService:
        return AsyncSessionService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    async def test_create_session_success(
        self,
        service: AsyncSessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=SESSIONS_AUTH_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "url": "https://ssio08.nchat.naver.com:443?auth=ASYNC_TOKEN",
                },
            },
        )

        response = await service.create_session()

        assert response.url == "https://ssio08.nchat.naver.com:443?auth=ASYNC_TOKEN"

    async def test_create_client_session_success(
        self,
        service: AsyncSessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=SESSIONS_AUTH_CLIENT_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "url": "https://ssio08.nchat.naver.com:443?auth=ASYNC_CLIENT_TOKEN",
                },
            },
        )

        response = await service.create_client_session()

        assert response.url == "https://ssio08.nchat.naver.com:443?auth=ASYNC_CLIENT_TOKEN"

    async def test_get_sessions_success(
        self,
        service: AsyncSessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_URL)}\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "sessionKey": "async_session_key",
                            "connectedDate": "2024-01-01T00:00:00Z",
                            "disconnectedDate": None,
                            "subscribedEvents": [
                                {"eventType": "DONATION", "channelId": "channel_2"},
                            ],
                        },
                    ],
                },
            },
        )

        sessions = await service.get_sessions()

        assert len(sessions) == 1
        assert sessions[0].session_key == "async_session_key"
        assert sessions[0].subscribed_events[0].event_type == EventType.DONATION

    async def test_subscribe_chat_success(
        self,
        service: AsyncSessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_SUBSCRIBE_CHAT_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        await service.subscribe_chat("async_session_key")

        request = httpx_mock.get_request()
        assert request is not None

    async def test_unsubscribe_chat_success(
        self,
        service: AsyncSessionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(rf"^{re.escape(SESSIONS_UNSUBSCRIBE_CHAT_URL)}\?.*"),
            method="POST",
            status_code=204,
        )

        await service.unsubscribe_chat("async_session_key")

        request = httpx_mock.get_request()
        assert request is not None
