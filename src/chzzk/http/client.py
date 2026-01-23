"""HTTP client wrapper for Chzzk API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from chzzk.constants import DEFAULT_TIMEOUT
from chzzk.http._base import BaseHTTPClient, extract_content, handle_error_response

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class HTTPClient(BaseHTTPClient[httpx.Client]):
    """Synchronous HTTP client for Chzzk API."""

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(timeout=timeout, headers=headers)
        self._client = httpx.Client(
            timeout=self._timeout,
            headers=self._headers,
        )

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
        response = self._client.post(url, params=params, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        logger.debug("GET %s params=%s", url, params)
        response = self._client.get(url, params=params, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        return extract_content(response.json())

    def put(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a PUT request and return JSON response."""
        logger.debug("PUT %s", url)
        response = self._client.put(url, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    def patch(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a PATCH request and return JSON response."""
        logger.debug("PATCH %s", url)
        response = self._client.patch(url, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    def delete(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a DELETE request and return JSON response."""
        logger.debug("DELETE %s", url)
        response = self._client.request("DELETE", url, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncHTTPClient(BaseHTTPClient[httpx.AsyncClient]):
    """Asynchronous HTTP client for Chzzk API."""

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(timeout=timeout, headers=headers)
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            headers=self._headers,
        )

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
        response = await self._client.post(url, params=params, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request and return JSON response."""
        logger.debug("GET %s params=%s", url, params)
        response = await self._client.get(url, params=params, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        return extract_content(response.json())

    async def put(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a PUT request and return JSON response."""
        logger.debug("PUT %s", url)
        response = await self._client.put(url, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    async def patch(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a PATCH request and return JSON response."""
        logger.debug("PATCH %s", url)
        response = await self._client.patch(url, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    async def delete(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a DELETE request and return JSON response."""
        logger.debug("DELETE %s", url)
        response = await self._client.request("DELETE", url, json=json, headers=headers)

        if response.status_code >= 400:
            handle_error_response(response)

        if response.status_code == 204 or not response.content:
            return {}

        return extract_content(response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
