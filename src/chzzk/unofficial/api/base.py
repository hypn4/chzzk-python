"""Base service class for unofficial API services."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chzzk.unofficial.http.client import AsyncUnofficialHTTPClient, UnofficialHTTPClient


class UnofficialBaseService:
    """Base class for synchronous unofficial API services."""

    def __init__(self, http_client: UnofficialHTTPClient) -> None:
        """Initialize the service.

        Args:
            http_client: Unofficial HTTP client instance.
        """
        self._http = http_client


class AsyncUnofficialBaseService:
    """Base class for asynchronous unofficial API services."""

    def __init__(self, http_client: AsyncUnofficialHTTPClient) -> None:
        """Initialize the async service.

        Args:
            http_client: Async unofficial HTTP client instance.
        """
        self._http = http_client
