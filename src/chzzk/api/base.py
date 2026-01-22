"""Base service class for API services."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chzzk.http.client import AsyncHTTPClient, HTTPClient


class BaseService:
    """Base class for synchronous API services."""

    def __init__(
        self,
        http_client: HTTPClient,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        token_refresher: Callable[[], str | None] | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            http_client: HTTP client instance for making requests.
            client_id: Client ID for API authentication.
            client_secret: Client secret for API authentication.
            access_token: Access token for user-authenticated requests.
            token_refresher: Optional callback to get/refresh access token.
        """
        self._http = http_client
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._token_refresher = token_refresher

    def _get_client_headers(self) -> dict[str, str]:
        """Get headers for Client-authenticated requests.

        Returns:
            Headers dict with Client-Id and Client-Secret.
        """
        headers: dict[str, str] = {}
        if self._client_id:
            headers["Client-Id"] = self._client_id
        if self._client_secret:
            headers["Client-Secret"] = self._client_secret
        return headers

    def _get_token_headers(self) -> dict[str, str]:
        """Get headers for Access Token-authenticated requests.

        If a token_refresher callback is configured, it will be called
        to get the current access token (and potentially refresh it).

        Returns:
            Headers dict with Authorization Bearer token.
        """
        # Use token refresher if available (may refresh expired token)
        if self._token_refresher:
            token = self._token_refresher()
            if token:
                self._access_token = token

        headers: dict[str, str] = {}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def set_access_token(self, token: str) -> None:
        """Update the access token.

        Args:
            token: New access token.
        """
        self._access_token = token


class AsyncBaseService:
    """Base class for asynchronous API services."""

    def __init__(
        self,
        http_client: AsyncHTTPClient,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        async_token_refresher: Callable[[], str | None] | None = None,
    ) -> None:
        """Initialize the async service.

        Args:
            http_client: Async HTTP client instance for making requests.
            client_id: Client ID for API authentication.
            client_secret: Client secret for API authentication.
            access_token: Access token for user-authenticated requests.
            async_token_refresher: Optional async callback to get/refresh access token.
        """
        self._http = http_client
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._async_token_refresher = async_token_refresher

    def _get_client_headers(self) -> dict[str, str]:
        """Get headers for Client-authenticated requests.

        Returns:
            Headers dict with Client-Id and Client-Secret.
        """
        headers: dict[str, str] = {}
        if self._client_id:
            headers["Client-Id"] = self._client_id
        if self._client_secret:
            headers["Client-Secret"] = self._client_secret
        return headers

    async def _get_token_headers(self) -> dict[str, str]:
        """Get headers for Access Token-authenticated requests.

        If an async_token_refresher callback is configured, it will be called
        to get the current access token (and potentially refresh it).

        Returns:
            Headers dict with Authorization Bearer token.
        """
        # Use async token refresher if available (may refresh expired token)
        if self._async_token_refresher:
            token = await self._async_token_refresher()
            if token:
                self._access_token = token

        headers: dict[str, str] = {}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def set_access_token(self, token: str) -> None:
        """Update the access token.

        Args:
            token: New access token.
        """
        self._access_token = token
