"""Tests for Category API service."""

from __future__ import annotations

import re

import pytest
from pytest_httpx import HTTPXMock

from chzzk.api.category import AsyncCategoryService, CategoryService
from chzzk.http.client import AsyncHTTPClient, HTTPClient
from chzzk.models import CategoryType


class TestCategoryService:
    """Tests for synchronous CategoryService."""

    @pytest.fixture
    def http_client(self) -> HTTPClient:
        return HTTPClient()

    @pytest.fixture
    def service(self, http_client: HTTPClient) -> CategoryService:
        return CategoryService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

    def test_search_success(
        self,
        service: CategoryService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/categories/search.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "categoryType": "GAME",
                            "categoryId": "game_001",
                            "categoryValue": "Test Game",
                            "posterImageUrl": "https://example.com/poster.jpg",
                        },
                        {
                            "categoryType": "ETC",
                            "categoryId": "etc_001",
                            "categoryValue": "Just Chatting",
                            "posterImageUrl": None,
                        },
                    ],
                },
            },
        )

        categories = service.search("game")

        assert len(categories) == 2
        assert categories[0].category_type == CategoryType.GAME
        assert categories[0].category_id == "game_001"
        assert categories[0].category_value == "Test Game"
        assert categories[0].poster_image_url == "https://example.com/poster.jpg"
        assert categories[1].category_type == CategoryType.ETC
        assert categories[1].poster_image_url is None

    def test_search_sends_client_headers(
        self,
        service: CategoryService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/categories/search.*"),
            method="GET",
            json={"code": 200, "content": {"data": []}},
        )

        service.search("test")

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Client-Id"] == "test_client_id"
        assert request.headers["Client-Secret"] == "test_client_secret"

    def test_search_with_size_parameter(
        self,
        service: CategoryService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/categories/search.*"),
            method="GET",
            json={"code": 200, "content": {"data": []}},
        )

        service.search("test", size=50)

        request = httpx_mock.get_request()
        assert request is not None
        assert "size=50" in str(request.url)


class TestAsyncCategoryService:
    """Tests for asynchronous AsyncCategoryService."""

    @pytest.fixture
    def http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    @pytest.fixture
    def service(self, http_client: AsyncHTTPClient) -> AsyncCategoryService:
        return AsyncCategoryService(
            http_client,
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

    async def test_search_success(
        self,
        service: AsyncCategoryService,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/categories/search.*"),
            method="GET",
            json={
                "code": 200,
                "content": {
                    "data": [
                        {
                            "categoryType": "SPORTS",
                            "categoryId": "sports_001",
                            "categoryValue": "Football",
                            "posterImageUrl": None,
                        },
                    ],
                },
            },
        )

        categories = await service.search("sports")

        assert len(categories) == 1
        assert categories[0].category_type == CategoryType.SPORTS
