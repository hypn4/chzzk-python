"""HTTP client wrapper for Chzzk API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from chzzk.exceptions import (
    ChzzkAPIError,
    ForbiddenError,
    InvalidClientError,
    InvalidTokenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_TIMEOUT = 30.0
USER_AGENT = "chzzk-python/0.1.0"


def _extract_content(data: Any) -> Any:
    """Extract content from Chzzk API response wrapper.

    Chzzk API wraps responses in { code, message, content }.
    This function extracts the actual content.
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
        if error_code == "INVALID_CLIENT":
            raise InvalidClientError(message)
        if error_code == "INVALID_TOKEN":
            raise InvalidTokenError(message)
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


class HTTPClient:
    """Synchronous HTTP client for Chzzk API."""

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        default_headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.Client(
            timeout=timeout,
            headers=default_headers,
        )

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request and return JSON response."""
        response = self._client.post(url, json=json, headers=headers)

        if response.status_code >= 400:
            _handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return _extract_content(response.json())

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        response = self._client.get(url, params=params, headers=headers)

        if response.status_code >= 400:
            _handle_error_response(response)

        return _extract_content(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncHTTPClient:
    """Asynchronous HTTP client for Chzzk API."""

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        default_headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=default_headers,
        )

    async def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request and return JSON response."""
        response = await self._client.post(url, json=json, headers=headers)

        if response.status_code >= 400:
            _handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return _extract_content(response.json())

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        response = await self._client.get(url, params=params, headers=headers)

        if response.status_code >= 400:
            _handle_error_response(response)

        return _extract_content(response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
