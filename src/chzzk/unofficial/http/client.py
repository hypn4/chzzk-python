"""HTTP client for unofficial Chzzk API with cookie support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from chzzk.constants import DEFAULT_TIMEOUT
from chzzk.unofficial.auth.cookie import NaverCookieAuth
from chzzk.unofficial.http._base import (
    BaseUnofficialHTTPClient,
    extract_content,
    handle_error_response,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class UnofficialHTTPClient(BaseUnofficialHTTPClient[httpx.Client]):
    """Synchronous HTTP client for unofficial Chzzk API with cookie support."""

    def __init__(
        self,
        auth: NaverCookieAuth | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the unofficial HTTP client.

        Args:
            auth: Naver cookie authentication.
            timeout: Request timeout in seconds.
            headers: Additional headers to include in requests.
        """
        super().__init__(auth, timeout=timeout, headers=headers)
        self._client = httpx.Client(
            timeout=self._timeout,
            headers=self._headers,
        )

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        logger.debug("GET %s params=%s", url, params)
        response = self._client.get(
            url,
            params=params,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            handle_error_response(response)

        return extract_content(response.json())

    def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request and return JSON response."""
        logger.debug("POST %s params=%s", url, params)
        response = self._client.post(
            url,
            params=params,
            json=json,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> UnofficialHTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncUnofficialHTTPClient(BaseUnofficialHTTPClient[httpx.AsyncClient]):
    """Asynchronous HTTP client for unofficial Chzzk API with cookie support."""

    def __init__(
        self,
        auth: NaverCookieAuth | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the async unofficial HTTP client.

        Args:
            auth: Naver cookie authentication.
            timeout: Request timeout in seconds.
            headers: Additional headers to include in requests.
        """
        super().__init__(auth, timeout=timeout, headers=headers)
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            headers=self._headers,
        )

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        logger.debug("GET %s params=%s", url, params)
        response = await self._client.get(
            url,
            params=params,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            handle_error_response(response)

        return extract_content(response.json())

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request and return JSON response."""
        logger.debug("POST %s params=%s", url, params)
        response = await self._client.post(
            url,
            params=params,
            json=json,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncUnofficialHTTPClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
