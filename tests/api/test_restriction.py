"""Tests for Restriction API service."""

from __future__ import annotations

import re

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.restriction import AsyncRestrictionService, RestrictionService
from chzzk.http import RESTRICT_CHANNELS_URL
from chzzk.http.client import AsyncHTTPClient, HTTPClient


class TestRestrictionService:
    """Tests for synchronous RestrictionService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> RestrictionService:
        return RestrictionService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_get_list_success(
        self,
        service: RestrictionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/restrict-channels.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "restrictedChannelId": "restricted_001",
                            "restrictedChannelName": "Restricted Channel",
                            "releaseDate": "2024-02-15T10:00:00Z",
                            "createdDate": "2024-01-15T10:00:00Z",
                        },
                        {
                            "restrictedChannelId": "restricted_002",
                            "restrictedChannelName": "Another Restricted",
                            "releaseDate": None,
                            "createdDate": "2024-01-10T08:00:00Z",
                        },
                    ],
                },
            },
        )

        channels = service.get_list()

        assert len(channels) == 2
        assert channels[0].restricted_channel_id == "restricted_001"
        assert channels[0].restricted_channel_name == "Restricted Channel"
        assert channels[0].release_date is not None
        assert channels[1].release_date is None

    def test_add_success(
        self,
        service: RestrictionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=RESTRICT_CHANNELS_URL,
            method="POST",
            status_code=204,
        )

        service.add("target_channel_id")

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "Bearer test_access_token"

    def test_remove_success(
        self,
        service: RestrictionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=RESTRICT_CHANNELS_URL,
            method="DELETE",
            status_code=204,
        )

        service.remove("target_channel_id")

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "Bearer test_access_token"


class TestAsyncRestrictionService:
    """Tests for asynchronous AsyncRestrictionService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncRestrictionService:
        return AsyncRestrictionService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    async def test_get_list_success(
        self,
        service: AsyncRestrictionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/restrict-channels.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "restrictedChannelId": "async_restricted_001",
                            "restrictedChannelName": "Async Restricted",
                            "releaseDate": None,
                            "createdDate": "2024-01-15T10:00:00Z",
                        },
                    ],
                },
            },
        )

        channels = await service.get_list()

        assert len(channels) == 1
        assert channels[0].restricted_channel_id == "async_restricted_001"

    async def test_add_success(
        self,
        service: AsyncRestrictionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=RESTRICT_CHANNELS_URL,
            method="POST",
            status_code=204,
        )

        await service.add("async_target_channel")

        request = httpx_mock.get_request()
        assert request is not None

    async def test_remove_success(
        self,
        service: AsyncRestrictionService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=RESTRICT_CHANNELS_URL,
            method="DELETE",
            status_code=204,
        )

        await service.remove("async_target_channel")

        request = httpx_mock.get_request()
        assert request is not None
