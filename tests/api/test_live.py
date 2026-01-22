"""Tests for Live API service."""

from __future__ import annotations

import re

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.live import AsyncLiveService, LiveService
from chzzk.http import LIVE_SETTING_URL, STREAM_KEY_URL
from chzzk.http.client import AsyncHTTPClient, HTTPClient
from chzzk.models import CategoryType


class TestLiveService:
    """Tests for synchronous LiveService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> LiveService:
        return LiveService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_get_lives_success(
        self,
        service: LiveService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/lives\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "liveId": 12345,
                            "liveTitle": "Test Stream",
                            "liveThumbnailImageUrl": "https://example.com/thumb.jpg",
                            "concurrentUserCount": 100,
                            "openDate": "2024-01-15T10:00:00Z",
                            "adult": False,
                            "tags": ["tag1", "tag2"],
                            "categoryType": "GAME",
                            "liveCategory": "game_001",
                            "liveCategoryValue": "Test Game",
                            "channelId": "channel_001",
                            "channelName": "Test Channel",
                            "channelImageUrl": "https://example.com/channel.jpg",
                        },
                    ],
                    "page": {"next": "next_token"},
                },
            },
        )

        response = service.get_lives()

        assert len(response.data) == 1
        assert response.data[0].live_id == 12345
        assert response.data[0].live_title == "Test Stream"
        assert response.data[0].concurrent_user_count == 100
        assert response.data[0].category_type == CategoryType.GAME
        assert response.page.next == "next_token"

    def test_get_stream_key_success(
        self,
        service: LiveService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=STREAM_KEY_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "streamKey": "test_stream_key_12345",
                },
            },
        )

        stream_key = service.get_stream_key()

        assert stream_key.stream_key == "test_stream_key_12345"

    def test_get_setting_success(
        self,
        service: LiveService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=LIVE_SETTING_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "defaultLiveTitle": "My Stream",
                    "category": {
                        "categoryType": "GAME",
                        "categoryId": "game_001",
                        "categoryValue": "Test Game",
                        "posterImageUrl": "https://example.com/poster.jpg",
                    },
                    "tags": ["tag1", "tag2"],
                },
            },
        )

        setting = service.get_setting()

        assert setting.default_live_title == "My Stream"
        assert setting.category is not None
        assert setting.category.category_type == CategoryType.GAME
        assert setting.tags == ["tag1", "tag2"]

    def test_update_setting_success(
        self,
        service: LiveService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=LIVE_SETTING_URL,
            method="PATCH",
            status_code=204,
        )

        service.update_setting(
            default_live_title="New Title",
            category_type=CategoryType.ETC,
            tags=["new_tag"],
        )

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "Bearer test_access_token"


class TestAsyncLiveService:
    """Tests for asynchronous AsyncLiveService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncLiveService:
        return AsyncLiveService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    async def test_get_lives_success(
        self,
        service: AsyncLiveService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/lives\?.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "liveId": 67890,
                            "liveTitle": "Async Stream",
                            "liveThumbnailImageUrl": None,
                            "concurrentUserCount": 50,
                            "openDate": "2024-01-15T12:00:00Z",
                            "adult": False,
                            "tags": [],
                            "categoryType": None,
                            "liveCategory": None,
                            "liveCategoryValue": None,
                            "channelId": "async_channel",
                            "channelName": "Async Channel",
                            "channelImageUrl": None,
                        },
                    ],
                    "page": {"next": None},
                },
            },
        )

        response = await service.get_lives()

        assert len(response.data) == 1
        assert response.data[0].live_id == 67890
        assert response.page.next is None
