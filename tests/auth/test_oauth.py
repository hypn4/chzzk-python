"""Tests for Chzzk OAuth client."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_httpx import HTTPXMock

from chzzk.auth import (
    AsyncChzzkOAuth,
    CallbackTokenStorage,
    ChzzkOAuth,
    FileTokenStorage,
    InMemoryTokenStorage,
    Token,
)
from chzzk.exceptions import (
    InvalidClientError,
    InvalidStateError,
    InvalidTokenError,
    RateLimitError,
    TokenExpiredError,
)
from chzzk.http import AUTH_REVOKE_URL, AUTH_TOKEN_URL


class TestInMemoryTokenStorage:
    """Tests for InMemoryTokenStorage."""

    def test_initial_state_is_none(self) -> None:
        storage = InMemoryTokenStorage()
        assert storage.get_token() is None

    def test_save_and_get_token(self) -> None:
        storage = InMemoryTokenStorage()
        token = Token(
            access_token="test_access",
            refresh_token="test_refresh",
            token_type="Bearer",
            expires_in=86400,
        )
        storage.save_token(token)
        assert storage.get_token() == token

    def test_delete_token(self) -> None:
        storage = InMemoryTokenStorage()
        token = Token(
            access_token="test_access",
            refresh_token="test_refresh",
            token_type="Bearer",
            expires_in=86400,
        )
        storage.save_token(token)
        storage.delete_token()
        assert storage.get_token() is None


class TestFileTokenStorage:
    """Tests for FileTokenStorage."""

    def test_get_token_file_not_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileTokenStorage(Path(tmpdir) / "nonexistent.json")
            assert storage.get_token() is None

    def test_save_and_get_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "token.json"
            storage = FileTokenStorage(file_path)

            token = Token(
                access_token="test_access",
                refresh_token="test_refresh",
                token_type="Bearer",
                expires_in=86400,
            )
            storage.save_token(token)

            loaded = storage.get_token()
            assert loaded is not None
            assert loaded.access_token == "test_access"
            assert loaded.refresh_token == "test_refresh"

    def test_delete_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "token.json"
            storage = FileTokenStorage(file_path)

            token = Token(
                access_token="test_access",
                refresh_token="test_refresh",
                token_type="Bearer",
                expires_in=86400,
            )
            storage.save_token(token)
            assert file_path.exists()

            storage.delete_token()
            assert not file_path.exists()
            assert storage.get_token() is None

    def test_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nested" / "dir" / "token.json"
            storage = FileTokenStorage(file_path)

            token = Token(
                access_token="test_access",
                refresh_token="test_refresh",
                token_type="Bearer",
                expires_in=86400,
            )
            storage.save_token(token)
            assert file_path.exists()


class TestCallbackTokenStorage:
    """Tests for CallbackTokenStorage."""

    def test_callbacks_are_called(self) -> None:
        mock_get = MagicMock(return_value=None)
        mock_save = MagicMock()
        mock_delete = MagicMock()

        storage = CallbackTokenStorage(
            get_callback=mock_get,
            save_callback=mock_save,
            delete_callback=mock_delete,
        )

        storage.get_token()
        mock_get.assert_called_once()

        token = Token(
            access_token="test",
            refresh_token="test",
            token_type="Bearer",
            expires_in=86400,
        )
        storage.save_token(token)
        mock_save.assert_called_once_with(token)

        storage.delete_token()
        mock_delete.assert_called_once()


class TestToken:
    """Tests for Token model."""

    def test_is_expired_when_token_is_valid(self) -> None:
        token = Token(
            access_token="test",
            refresh_token="test",
            token_type="Bearer",
            expires_in=86400,
            issued_at=datetime.now(UTC),
        )
        assert not token.is_expired

    def test_is_expired_when_token_is_expired(self) -> None:
        token = Token(
            access_token="test",
            refresh_token="test",
            token_type="Bearer",
            expires_in=86400,
            issued_at=datetime.now(UTC) - timedelta(days=2),
        )
        assert token.is_expired

    def test_is_expired_within_buffer(self) -> None:
        token = Token(
            access_token="test",
            refresh_token="test",
            token_type="Bearer",
            expires_in=30,
            issued_at=datetime.now(UTC),
        )
        assert token.is_expired

    def test_expires_at_calculation(self) -> None:
        issued = datetime.now(UTC)
        token = Token(
            access_token="test",
            refresh_token="test",
            token_type="Bearer",
            expires_in=3600,
            issued_at=issued,
        )
        expected = issued + timedelta(seconds=3600)
        assert token.expires_at == expected


class TestChzzkOAuth:
    """Tests for synchronous ChzzkOAuth client."""

    @pytest.fixture
    def oauth(self) -> ChzzkOAuth:
        return ChzzkOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
        )

    def test_get_authorization_url(self, oauth: ChzzkOAuth) -> None:
        url, state = oauth.get_authorization_url()

        assert "https://chzzk.naver.com/account-interlock" in url
        assert "clientId=test_client_id" in url
        assert f"state={state}" in url
        assert "redirectUri=http%3A%2F%2Flocalhost%3A8080%2Fcallback" in url
        assert len(state) > 0

    def test_get_authorization_url_with_custom_state(self, oauth: ChzzkOAuth) -> None:
        url, state = oauth.get_authorization_url(state="custom_state")

        assert state == "custom_state"
        assert "state=custom_state" in url

    def test_exchange_code_success(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "new_access_token",
                "refreshToken": "new_refresh_token",
                "tokenType": "Bearer",
                "expiresIn": 86400,
            },
        )

        _, state = oauth.get_authorization_url()
        token = oauth.exchange_code(code="auth_code", state=state)

        assert token.access_token == "new_access_token"
        assert token.refresh_token == "new_refresh_token"
        assert token.token_type == "Bearer"
        assert oauth.get_token() is not None

    def test_exchange_code_state_mismatch(self, oauth: ChzzkOAuth) -> None:
        oauth.get_authorization_url(state="expected_state")

        with pytest.raises(InvalidStateError):
            oauth.exchange_code(code="auth_code", state="wrong_state")

    def test_exchange_code_skip_state_validation(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "token",
                "refreshToken": "refresh",
                "tokenType": "Bearer",
                "expiresIn": 86400,
            },
        )

        oauth.get_authorization_url(state="expected_state")
        token = oauth.exchange_code(
            code="auth_code",
            state="any_state",
            validate_state=False,
        )

        assert token.access_token == "token"

    def test_refresh_token_success(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "refreshed_access_token",
                "refreshToken": "new_refresh_token",
                "tokenType": "Bearer",
                "expiresIn": 86400,
                "scope": "channel",
            },
        )

        initial_token = Token(
            access_token="old_access",
            refresh_token="old_refresh",
            token_type="Bearer",
            expires_in=86400,
        )
        oauth._storage.save_token(initial_token)

        token = oauth.refresh_token()

        assert token.access_token == "refreshed_access_token"
        assert token.refresh_token == "new_refresh_token"

    def test_refresh_token_no_token_available(self, oauth: ChzzkOAuth) -> None:
        with pytest.raises(TokenExpiredError):
            oauth.refresh_token()

    def test_revoke_token_success(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_REVOKE_URL,
            method="POST",
            status_code=204,
        )

        token = Token(
            access_token="to_revoke",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=86400,
        )
        oauth._storage.save_token(token)

        oauth.revoke_token()

        assert oauth.get_token() is None

    def test_revoke_token_no_token_does_nothing(self, oauth: ChzzkOAuth) -> None:
        oauth.revoke_token()

    def test_get_access_token_returns_valid_token(self, oauth: ChzzkOAuth) -> None:
        token = Token(
            access_token="valid_token",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=86400,
            issued_at=datetime.now(UTC),
        )
        oauth._storage.save_token(token)

        access_token = oauth.get_access_token()
        assert access_token == "valid_token"

    def test_get_access_token_auto_refresh(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "refreshed_token",
                "refreshToken": "new_refresh",
                "tokenType": "Bearer",
                "expiresIn": 86400,
            },
        )

        expired_token = Token(
            access_token="expired_token",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=86400,
            issued_at=datetime.now(UTC) - timedelta(days=2),
        )
        oauth._storage.save_token(expired_token)

        access_token = oauth.get_access_token(auto_refresh=True)
        assert access_token == "refreshed_token"

    def test_get_access_token_expired_no_auto_refresh(self, oauth: ChzzkOAuth) -> None:
        expired_token = Token(
            access_token="expired_token",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=86400,
            issued_at=datetime.now(UTC) - timedelta(days=2),
        )
        oauth._storage.save_token(expired_token)

        with pytest.raises(InvalidTokenError):
            oauth.get_access_token(auto_refresh=False)

    def test_get_access_token_no_token(self, oauth: ChzzkOAuth) -> None:
        with pytest.raises(TokenExpiredError):
            oauth.get_access_token()

    def test_invalid_client_error(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            status_code=401,
            json={"code": "INVALID_CLIENT", "message": "Invalid client"},
        )

        _, state = oauth.get_authorization_url()
        with pytest.raises(InvalidClientError):
            oauth.exchange_code(code="code", state=state)

    def test_rate_limit_error(
        self,
        oauth: ChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            status_code=429,
            json={"code": "TOO_MANY_REQUESTS", "message": "Rate limited"},
        )

        _, state = oauth.get_authorization_url()
        with pytest.raises(RateLimitError):
            oauth.exchange_code(code="code", state=state)

    def test_context_manager(self) -> None:
        with ChzzkOAuth(
            client_id="test",
            client_secret="secret",
            redirect_uri="http://localhost",
        ) as oauth:
            url, _ = oauth.get_authorization_url()
            assert "https://chzzk.naver.com" in url


class TestAsyncChzzkOAuth:
    """Tests for asynchronous AsyncChzzkOAuth client."""

    @pytest.fixture
    def oauth(self) -> AsyncChzzkOAuth:
        return AsyncChzzkOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
        )

    def test_get_authorization_url(self, oauth: AsyncChzzkOAuth) -> None:
        url, state = oauth.get_authorization_url()

        assert "https://chzzk.naver.com/account-interlock" in url
        assert "clientId=test_client_id" in url
        assert f"state={state}" in url

    async def test_exchange_code_success(
        self,
        oauth: AsyncChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "new_access_token",
                "refreshToken": "new_refresh_token",
                "tokenType": "Bearer",
                "expiresIn": 86400,
            },
        )

        _, state = oauth.get_authorization_url()
        token = await oauth.exchange_code(code="auth_code", state=state)

        assert token.access_token == "new_access_token"
        assert token.refresh_token == "new_refresh_token"

    async def test_refresh_token_success(
        self,
        oauth: AsyncChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "refreshed_token",
                "refreshToken": "new_refresh",
                "tokenType": "Bearer",
                "expiresIn": 86400,
            },
        )

        initial = Token(
            access_token="old",
            refresh_token="old_refresh",
            token_type="Bearer",
            expires_in=86400,
        )
        oauth._storage.save_token(initial)

        token = await oauth.refresh_token()
        assert token.access_token == "refreshed_token"

    async def test_revoke_token_success(
        self,
        oauth: AsyncChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_REVOKE_URL,
            method="POST",
            status_code=204,
        )

        token = Token(
            access_token="to_revoke",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=86400,
        )
        oauth._storage.save_token(token)

        await oauth.revoke_token()
        assert oauth.get_token() is None

    async def test_get_access_token_auto_refresh(
        self,
        oauth: AsyncChzzkOAuth,
        httpx_mock: HTTPXMock,
    ) -> None:
        httpx_mock.add_response(
            url=AUTH_TOKEN_URL,
            method="POST",
            json={
                "accessToken": "refreshed_token",
                "refreshToken": "new_refresh",
                "tokenType": "Bearer",
                "expiresIn": 86400,
            },
        )

        expired = Token(
            access_token="expired",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=86400,
            issued_at=datetime.now(UTC) - timedelta(days=2),
        )
        oauth._storage.save_token(expired)

        access_token = await oauth.get_access_token()
        assert access_token == "refreshed_token"

    async def test_context_manager(self, httpx_mock: HTTPXMock) -> None:
        async with AsyncChzzkOAuth(
            client_id="test",
            client_secret="secret",
            redirect_uri="http://localhost",
        ) as oauth:
            url, _ = oauth.get_authorization_url()
            assert "https://chzzk.naver.com" in url
