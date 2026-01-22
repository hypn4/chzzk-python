"""Tests for User API service."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.user import AsyncUserService, UserService
from chzzk.http import USER_ME_URL
from chzzk.http.client import AsyncHTTPClient, HTTPClient


class TestUserService:
    """Tests for synchronous UserService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> UserService:
        return UserService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_get_me_success(
        self,
        service: UserService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=USER_ME_URL,
            method="GET",
            json={
                "code": 200,
                "message": None,
                "content": {
                    "channelId": "test_channel_id",
                    "channelName": "test_channel_name",
                },
            },
        )

        user = service.get_me()

        assert user.channel_id == "test_channel_id"
        assert user.channel_name == "test_channel_name"

    def test_get_me_sends_authorization_header(
        self,
        service: UserService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=USER_ME_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "channelId": "test_channel_id",
                    "channelName": "test_channel_name",
                },
            },
        )

        service.get_me()

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "Bearer test_access_token"


class TestAsyncUserService:
    """Tests for asynchronous AsyncUserService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncUserService:
        return AsyncUserService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    async def test_get_me_success(
        self,
        service: AsyncUserService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=USER_ME_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "channelId": "async_channel_id",
                    "channelName": "async_channel_name",
                },
            },
        )

        user = await service.get_me()

        assert user.channel_id == "async_channel_id"
        assert user.channel_name == "async_channel_name"
