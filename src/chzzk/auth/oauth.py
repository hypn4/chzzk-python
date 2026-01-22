"""OAuth client for Chzzk authentication."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from urllib.parse import urlencode

from chzzk.auth.models import (
    AuthorizationCodeRequest,
    RefreshTokenRequest,
    RevokeTokenRequest,
    Token,
    TokenResponse,
    TokenTypeHint,
)
from chzzk.exceptions import InvalidStateError, TokenExpiredError
from chzzk.http import AUTH_INTERLOCK_URL, AUTH_REVOKE_URL, AUTH_TOKEN_URL
from chzzk.http.client import AsyncHTTPClient, HTTPClient

if TYPE_CHECKING:
    pass


@runtime_checkable
class TokenStorage(Protocol):
    """Protocol for token storage implementations."""

    def get_token(self) -> Token | None:
        """Retrieve the stored token."""
        ...

    def save_token(self, token: Token) -> None:
        """Save a token."""
        ...

    def delete_token(self) -> None:
        """Delete the stored token."""
        ...


class InMemoryTokenStorage:
    """In-memory token storage implementation."""

    def __init__(self) -> None:
        self._token: Token | None = None

    def get_token(self) -> Token | None:
        """Retrieve the stored token."""
        return self._token

    def save_token(self, token: Token) -> None:
        """Save a token."""
        self._token = token

    def delete_token(self) -> None:
        """Delete the stored token."""
        self._token = None


class ChzzkOAuth:
    """Synchronous OAuth client for Chzzk authentication.

    This client handles the OAuth 2.0 authorization code flow for Chzzk,
    including token exchange, refresh, and revocation.

    Example:
        >>> oauth = ChzzkOAuth(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     redirect_uri="http://localhost:8080/callback",
        ... )
        >>> auth_url, state = oauth.get_authorization_url()
        >>> # User visits auth_url and gets redirected back with code
        >>> token = oauth.exchange_code(code="auth_code", state=state)
        >>> access_token = token.access_token
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        token_storage: TokenStorage | None = None,
    ) -> None:
        """Initialize the OAuth client.

        Args:
            client_id: Your Chzzk application's client ID.
            client_secret: Your Chzzk application's client secret.
            redirect_uri: The redirect URI registered with your application.
            token_storage: Optional custom token storage. Defaults to InMemoryTokenStorage.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._storage = token_storage or InMemoryTokenStorage()
        self._http = HTTPClient()
        self._pending_state: str | None = None

    def get_authorization_url(self, *, state: str | None = None) -> tuple[str, str]:
        """Generate the authorization URL for user authentication.

        Args:
            state: Optional state parameter. If not provided, a random one is generated.

        Returns:
            A tuple of (authorization_url, state).
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        self._pending_state = state

        params = {
            "clientId": self.client_id,
            "redirectUri": self.redirect_uri,
            "state": state,
        }

        url = f"{AUTH_INTERLOCK_URL}?{urlencode(params)}"
        return url, state

    def exchange_code(
        self,
        code: str,
        state: str,
        *,
        validate_state: bool = True,
    ) -> Token:
        """Exchange an authorization code for access and refresh tokens.

        Args:
            code: The authorization code received from the callback.
            state: The state parameter received from the callback.
            validate_state: Whether to validate the state parameter. Defaults to True.

        Returns:
            The Token object containing access and refresh tokens.

        Raises:
            InvalidStateError: If state validation fails.
        """
        if validate_state and self._pending_state and state != self._pending_state:
            raise InvalidStateError(
                f"State mismatch: expected '{self._pending_state}', got '{state}'"
            )

        request = AuthorizationCodeRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code,
            state=state,
        )

        response_data = self._http.post(
            AUTH_TOKEN_URL,
            json=request.model_dump(by_alias=True),
        )

        token_response = TokenResponse.model_validate(response_data)
        token = Token.from_response(token_response)
        self._storage.save_token(token)
        self._pending_state = None

        return token

    def refresh_token(self, refresh_token: str | None = None) -> Token:
        """Refresh the access token using a refresh token.

        Args:
            refresh_token: Optional refresh token to use. If not provided,
                uses the stored token's refresh token.

        Returns:
            The new Token object.

        Raises:
            TokenExpiredError: If no refresh token is available.
        """
        if refresh_token is None:
            stored_token = self._storage.get_token()
            if stored_token is None:
                raise TokenExpiredError("No token available for refresh")
            refresh_token = stored_token.refresh_token

        request = RefreshTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=refresh_token,
        )

        response_data = self._http.post(
            AUTH_TOKEN_URL,
            json=request.model_dump(by_alias=True),
        )

        token_response = TokenResponse.model_validate(response_data)
        token = Token.from_response(token_response)
        self._storage.save_token(token)

        return token

    def revoke_token(
        self,
        token: str | None = None,
        token_type_hint: TokenTypeHint = TokenTypeHint.ACCESS_TOKEN,
    ) -> None:
        """Revoke a token.

        This revokes both access and refresh tokens associated with the same
        authentication (same client_id and user).

        Args:
            token: Optional token to revoke. If not provided, uses the stored access token.
            token_type_hint: The type of token being revoked.
        """
        if token is None:
            stored_token = self._storage.get_token()
            if stored_token is None:
                return
            token = stored_token.access_token

        request = RevokeTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token=token,
            token_type_hint=token_type_hint,
        )

        self._http.post(
            AUTH_REVOKE_URL,
            json=request.model_dump(by_alias=True),
        )

        self._storage.delete_token()

    def get_token(self) -> Token | None:
        """Get the stored token.

        Returns:
            The stored Token object or None if no token is stored.
        """
        return self._storage.get_token()

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> ChzzkOAuth:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncChzzkOAuth:
    """Asynchronous OAuth client for Chzzk authentication.

    This client handles the OAuth 2.0 authorization code flow for Chzzk,
    including token exchange, refresh, and revocation.

    Example:
        >>> async with AsyncChzzkOAuth(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     redirect_uri="http://localhost:8080/callback",
        ... ) as oauth:
        ...     auth_url, state = oauth.get_authorization_url()
        ...     # User visits auth_url and gets redirected back with code
        ...     token = await oauth.exchange_code(code="auth_code", state=state)
        ...     access_token = token.access_token
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        token_storage: TokenStorage | None = None,
    ) -> None:
        """Initialize the async OAuth client.

        Args:
            client_id: Your Chzzk application's client ID.
            client_secret: Your Chzzk application's client secret.
            redirect_uri: The redirect URI registered with your application.
            token_storage: Optional custom token storage. Defaults to InMemoryTokenStorage.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._storage = token_storage or InMemoryTokenStorage()
        self._http = AsyncHTTPClient()
        self._pending_state: str | None = None

    def get_authorization_url(self, *, state: str | None = None) -> tuple[str, str]:
        """Generate the authorization URL for user authentication.

        Args:
            state: Optional state parameter. If not provided, a random one is generated.

        Returns:
            A tuple of (authorization_url, state).
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        self._pending_state = state

        params = {
            "clientId": self.client_id,
            "redirectUri": self.redirect_uri,
            "state": state,
        }

        url = f"{AUTH_INTERLOCK_URL}?{urlencode(params)}"
        return url, state

    async def exchange_code(
        self,
        code: str,
        state: str,
        *,
        validate_state: bool = True,
    ) -> Token:
        """Exchange an authorization code for access and refresh tokens.

        Args:
            code: The authorization code received from the callback.
            state: The state parameter received from the callback.
            validate_state: Whether to validate the state parameter. Defaults to True.

        Returns:
            The Token object containing access and refresh tokens.

        Raises:
            InvalidStateError: If state validation fails.
        """
        if validate_state and self._pending_state and state != self._pending_state:
            raise InvalidStateError(
                f"State mismatch: expected '{self._pending_state}', got '{state}'"
            )

        request = AuthorizationCodeRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code,
            state=state,
        )

        response_data = await self._http.post(
            AUTH_TOKEN_URL,
            json=request.model_dump(by_alias=True),
        )

        token_response = TokenResponse.model_validate(response_data)
        token = Token.from_response(token_response)
        self._storage.save_token(token)
        self._pending_state = None

        return token

    async def refresh_token(self, refresh_token: str | None = None) -> Token:
        """Refresh the access token using a refresh token.

        Args:
            refresh_token: Optional refresh token to use. If not provided,
                uses the stored token's refresh token.

        Returns:
            The new Token object.

        Raises:
            TokenExpiredError: If no refresh token is available.
        """
        if refresh_token is None:
            stored_token = self._storage.get_token()
            if stored_token is None:
                raise TokenExpiredError("No token available for refresh")
            refresh_token = stored_token.refresh_token

        request = RefreshTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=refresh_token,
        )

        response_data = await self._http.post(
            AUTH_TOKEN_URL,
            json=request.model_dump(by_alias=True),
        )

        token_response = TokenResponse.model_validate(response_data)
        token = Token.from_response(token_response)
        self._storage.save_token(token)

        return token

    async def revoke_token(
        self,
        token: str | None = None,
        token_type_hint: TokenTypeHint = TokenTypeHint.ACCESS_TOKEN,
    ) -> None:
        """Revoke a token.

        This revokes both access and refresh tokens associated with the same
        authentication (same client_id and user).

        Args:
            token: Optional token to revoke. If not provided, uses the stored access token.
            token_type_hint: The type of token being revoked.
        """
        if token is None:
            stored_token = self._storage.get_token()
            if stored_token is None:
                return
            token = stored_token.access_token

        request = RevokeTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token=token,
            token_type_hint=token_type_hint,
        )

        await self._http.post(
            AUTH_REVOKE_URL,
            json=request.model_dump(by_alias=True),
        )

        self._storage.delete_token()

    def get_token(self) -> Token | None:
        """Get the stored token.

        Returns:
            The stored Token object or None if no token is stored.
        """
        return self._storage.get_token()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.close()

    async def __aenter__(self) -> AsyncChzzkOAuth:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
