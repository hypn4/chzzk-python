"""Tests for Channel API service."""

from __future__ import annotations

import re

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.channel import AsyncChannelService, ChannelService
from chzzk.http import CHANNEL_ROLES_URL
from chzzk.http.client import AsyncHTTPClient, HTTPClient
from chzzk.models import SubscriberSortType, UserRole


class TestChannelService:
    """Tests for synchronous ChannelService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> ChannelService:
        return ChannelService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_get_channels_success(
        self,
        service: ChannelService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/channels\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "channelId": "channel_001",
                            "channelName": "Test Channel",
                            "channelImageUrl": "https://example.com/image.jpg",
                            "followerCount": 1000,
                            "verifiedMark": True,
                        },
                    ],
                },
            },
        )

        channels = service.get_channels(["channel_001"])

        assert len(channels) == 1
        assert channels[0].channel_id == "channel_001"
        assert channels[0].channel_name == "Test Channel"
        assert channels[0].follower_count == 1000
        assert channels[0].verified_mark is True

    def test_get_channels_sends_client_headers(
        self,
        service: ChannelService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/channels\?.*"),
            method="GET",
            json={"code": 200, "content": {"data": []}},
        )

        service.get_channels(["channel_001"])

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Client-Id"] == "test_client_id"
        assert request.headers["Client-Secret"] == "test_client_secret"

    def test_get_streaming_roles_success(
        self,
        service: ChannelService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=CHANNEL_ROLES_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "managerChannelId": "manager_001",
                            "managerChannelName": "Manager Name",
                            "userRole": "STREAMING_CHANNEL_MANAGER",
                            "createdDate": "2024-01-15T10:30:00Z",
                        },
                    ],
                },
            },
        )

        managers = service.get_streaming_roles()

        assert len(managers) == 1
        assert managers[0].manager_channel_id == "manager_001"
        assert managers[0].user_role == UserRole.STREAMING_CHANNEL_MANAGER

    def test_get_followers_success(
        self,
        service: ChannelService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/channels/followers.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "channelId": "follower_001",
                            "channelName": "Follower Name",
                            "createdDate": "2024-01-10T08:00:00Z",
                        },
                    ],
                },
            },
        )

        followers = service.get_followers()

        assert len(followers) == 1
        assert followers[0].channel_id == "follower_001"
        assert followers[0].channel_name == "Follower Name"

    def test_get_subscribers_success(
        self,
        service: ChannelService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/channels/subscribers.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "channelId": "subscriber_001",
                            "channelName": "Subscriber Name",
                            "createdDate": "2024-01-05T12:00:00Z",
                            "tierNo": 1,
                            "month": 3,
                        },
                    ],
                },
            },
        )

        subscribers = service.get_subscribers(sort=SubscriberSortType.LONGER)

        assert len(subscribers) == 1
        assert subscribers[0].channel_id == "subscriber_001"
        assert subscribers[0].tier_no == 1
        assert subscribers[0].month == 3


class TestAsyncChannelService:
    """Tests for asynchronous AsyncChannelService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncChannelService:
        return AsyncChannelService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    async def test_get_channels_success(
        self,
        service: AsyncChannelService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/channels\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "channelId": "async_channel_001",
                            "channelName": "Async Channel",
                            "channelImageUrl": None,
                            "followerCount": 500,
                            "verifiedMark": False,
                        },
                    ],
                },
            },
        )

        channels = await service.get_channels(["async_channel_001"])

        assert len(channels) == 1
        assert channels[0].channel_id == "async_channel_001"
