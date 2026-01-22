"""Tests for unified ChzzkClient."""

from __future__ import annotations

import re

import pytest
from pytest_httpx import HTTPXMock

from chzzk.client import AsyncChzzkClient, ChzzkClient
from chzzk.http import AUTH_TOKEN_URL, USER_ME_URL


class TestChzzkClient:
    """Tests for synchronous ChzzkClient."""

    @pytest.fixture
    def client(self) -> ChzzkClient:
        return ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_client_has_all_services(self, client: ChzzkClient) -> None:
        assert hasattr(client, "user")
        assert hasattr(client, "channel")
        assert hasattr(client, "category")
        assert hasattr(client, "live")
        assert hasattr(client, "chat")
        assert hasattr(client, "restriction")

    def test_set_access_token_updates_all_services(self, client: ChzzkClient) -> None:
        new_token = "new_access_token"
        client.set_access_token(new_token)

        assert client.user._access_token == new_token
        assert client.channel._access_token == new_token
        assert client.category._access_token == new_token
        assert client.live._access_token == new_token
        assert client.chat._access_token == new_token
        assert client.restriction._access_token == new_token

    def test_context_manager(self) -> None:
        with ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        ) as client:
            assert client is not None

    def test_user_service_works(
        self,
        client: ChzzkClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=USER_ME_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "channelId": "test_channel",
                    "channelName": "Test Channel",
                },
            },
        )

        user = client.user.get_me()

        assert user.channel_id == "test_channel"

    def test_category_service_works(
        self,
        client: ChzzkClient,
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
                            "posterImageUrl": None,
                        },
                    ],
                },
            },
        )

        categories = client.category.search("test")

        assert len(categories) == 1


class TestChzzkClientOAuth:
    """Tests for ChzzkClient OAuth integration."""

    @pytest.fixture
    def oauth_client(self) -> ChzzkClient:
        return ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
        )

    def test_oauth_client_has_oauth(self, oauth_client: ChzzkClient) -> None:
        assert oauth_client._oauth is not None

    def test_non_oauth_client_has_no_oauth(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        assert client._oauth is None

    def test_get_authorization_url(self, oauth_client: ChzzkClient) -> None:
        auth_url, state = oauth_client.get_authorization_url()

        assert "chzzk.naver.com" in auth_url
        assert "clientId=test_client_id" in auth_url
        assert f"state={state}" in auth_url
        assert len(state) > 0

    def test_get_authorization_url_without_redirect_uri_raises(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            client.get_authorization_url()

    def test_authenticate(
        self,
        oauth_client: ChzzkClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "new_access_token",
                "refreshToken": "new_refresh_token",
                "tokenType": "Bearer",
                "expiresIn": 3600,
            },
        )

        # Get authorization URL to set pending state
        _, state = oauth_client.get_authorization_url()

        token = oauth_client.authenticate(code="test_code", state=state)

        assert token.access_token == "new_access_token"
        assert oauth_client._access_token == "new_access_token"
        assert oauth_client.user._access_token == "new_access_token"

    def test_authenticate_without_redirect_uri_raises(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            client.authenticate(code="test_code", state="test_state")

    def test_is_authenticated_with_access_token(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="some_token",
        )
        assert client.is_authenticated is True

    def test_is_authenticated_without_token(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        assert client.is_authenticated is False

    def test_refresh_token_without_redirect_uri_raises(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            client.refresh_token()

    def test_revoke_token_without_redirect_uri_raises(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            client.revoke_token()

    def test_get_token_without_oauth_returns_none(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        assert client.get_token() is None


class TestChzzkClientAutoRefresh:
    """Tests for automatic token refresh."""

    def test_token_refresher_is_created_when_oauth_enabled(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            auto_refresh=True,
        )
        assert client.user._token_refresher is not None

    def test_token_refresher_not_created_when_disabled(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            auto_refresh=False,
        )
        assert client.user._token_refresher is None

    def test_token_refresher_not_created_without_redirect_uri(self) -> None:
        client = ChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        assert client.user._token_refresher is None


class TestAsyncChzzkClient:
    """Tests for asynchronous AsyncChzzkClient."""

    @pytest.fixture
    def client(self) -> AsyncChzzkClient:
        return AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_access_token",
        )

    def test_client_has_all_services(self, client: AsyncChzzkClient) -> None:
        assert hasattr(client, "user")
        assert hasattr(client, "channel")
        assert hasattr(client, "category")
        assert hasattr(client, "live")
        assert hasattr(client, "chat")
        assert hasattr(client, "restriction")

    def test_set_access_token_updates_all_services(self, client: AsyncChzzkClient) -> None:
        new_token = "new_access_token"
        client.set_access_token(new_token)

        assert client.user._access_token == new_token
        assert client.channel._access_token == new_token

    async def test_context_manager(self) -> None:
        async with AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        ) as client:
            assert client is not None

    async def test_user_service_works(
        self,
        client: AsyncChzzkClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=USER_ME_URL,
            method="GET",
            json={
                "code": 200,
                "content": {
                    "channelId": "async_test_channel",
                    "channelName": "Async Test Channel",
                },
            },
        )

        user = await client.user.get_me()

        assert user.channel_id == "async_test_channel"

    async def test_category_service_works(
        self,
        client: AsyncChzzkClient,
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
                            "categoryType": "ETC",
                            "categoryId": "etc_001",
                            "categoryValue": "Just Chatting",
                            "posterImageUrl": None,
                        },
                    ],
                },
            },
        )

        categories = await client.category.search("chat")

        assert len(categories) == 1


class TestAsyncChzzkClientOAuth:
    """Tests for AsyncChzzkClient OAuth integration."""

    @pytest.fixture
    def oauth_client(self) -> AsyncChzzkClient:
        return AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
        )

    def test_oauth_client_has_oauth(self, oauth_client: AsyncChzzkClient) -> None:
        assert oauth_client._oauth is not None

    def test_non_oauth_client_has_no_oauth(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        assert client._oauth is None

    def test_get_authorization_url(self, oauth_client: AsyncChzzkClient) -> None:
        auth_url, state = oauth_client.get_authorization_url()

        assert "chzzk.naver.com" in auth_url
        assert "clientId=test_client_id" in auth_url
        assert f"state={state}" in auth_url

    def test_get_authorization_url_without_redirect_uri_raises(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            client.get_authorization_url()

    async def test_authenticate(
        self,
        oauth_client: AsyncChzzkClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "new_access_token",
                "refreshToken": "new_refresh_token",
                "tokenType": "Bearer",
                "expiresIn": 3600,
            },
        )

        # Get authorization URL to set pending state
        _, state = oauth_client.get_authorization_url()

        token = await oauth_client.authenticate(code="test_code", state=state)

        assert token.access_token == "new_access_token"
        assert oauth_client._access_token == "new_access_token"

    async def test_authenticate_without_redirect_uri_raises(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            await client.authenticate(code="test_code", state="test_state")

    def test_is_authenticated_with_access_token(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="some_token",
        )
        assert client.is_authenticated is True

    async def test_refresh_token_without_redirect_uri_raises(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            await client.refresh_token()

    async def test_revoke_token_without_redirect_uri_raises(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
        )
        with pytest.raises(ValueError, match="redirect_uri is required"):
            await client.revoke_token()

    def test_async_token_refresher_is_created_when_oauth_enabled(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            auto_refresh=True,
        )
        assert client.user._async_token_refresher is not None

    def test_async_token_refresher_not_created_when_disabled(self) -> None:
        client = AsyncChzzkClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            auto_refresh=False,
        )
        assert client.user._async_token_refresher is None
