"""HTTP client for unofficial Chzzk API with cookie support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from chzzk.exceptions import (
    ChzzkAPIError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from chzzk.unofficial.auth.cookie import NaverCookieAuth

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_TIMEOUT = 30.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _extract_content(data: Any) -> Any:
    """Extract content from Chzzk API response wrapper.

    Chzzk API wraps responses in { code, message, content }.
    """
    if isinstance(data, dict) and "content" in data:
        return data["content"]
    return data


def _handle_error_response(response: httpx.Response) -> None:
    """Raise appropriate exception based on response status and content."""
    status_code = response.status_code

    try:
        data = response.json()
        error_code = data.get("code") or data.get("error")
        message = data.get("message") or data.get("error_description") or str(data)
    except Exception:
        error_code = None
        message = response.text or f"HTTP {status_code}"

    if status_code == 401:
        raise ChzzkAPIError(message, status_code=401, error_code=error_code)

    if status_code == 403:
        raise ForbiddenError(message)

    if status_code == 404:
        raise NotFoundError(message)

    if status_code == 429:
        raise RateLimitError(message)

    if status_code >= 500:
        raise ServerError(message)

    raise ChzzkAPIError(message, status_code=status_code, error_code=error_code)


class UnofficialHTTPClient:
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
        self._auth = auth

        default_headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://chzzk.naver.com/",
            "Origin": "https://chzzk.naver.com",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.Client(
            timeout=timeout,
            headers=default_headers,
        )

    def _get_cookies(self) -> dict[str, str]:
        """Get cookies from auth if available."""
        if self._auth:
            return self._auth.get_cookies()
        return {}

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        response = self._client.get(
            url,
            params=params,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            _handle_error_response(response)

        return _extract_content(response.json())

    def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request and return JSON response."""
        response = self._client.post(
            url,
            params=params,
            json=json,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            _handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return _extract_content(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> UnofficialHTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncUnofficialHTTPClient:
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
        self._auth = auth

        default_headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://chzzk.naver.com/",
            "Origin": "https://chzzk.naver.com",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=default_headers,
        )

    def _get_cookies(self) -> dict[str, str]:
        """Get cookies from auth if available."""
        if self._auth:
            return self._auth.get_cookies()
        return {}

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        response = await self._client.get(
            url,
            params=params,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            _handle_error_response(response)

        return _extract_content(response.json())

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request and return JSON response."""
        response = await self._client.post(
            url,
            params=params,
            json=json,
            headers=headers,
            cookies=self._get_cookies(),
        )

        if response.status_code >= 400:
            _handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return _extract_content(response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncUnofficialHTTPClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
