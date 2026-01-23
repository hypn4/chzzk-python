"""Base HTTP client functionality for unofficial API."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from chzzk.constants import DEFAULT_TIMEOUT, UNOFFICIAL_USER_AGENT, HTTPStatus
from chzzk.exceptions import (
    ChzzkAPIError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from chzzk.unofficial.auth.cookie import NaverCookieAuth

logger = logging.getLogger(__name__)


def extract_content(data: Any) -> Any:
    """Extract content from Chzzk API response wrapper.

    Chzzk API wraps responses in { code, message, content }.
    """
    if isinstance(data, dict) and "content" in data:
        return data["content"]
    return data


def handle_error_response(response: httpx.Response) -> None:
    """Raise appropriate exception based on response status and content."""
    status_code = response.status_code

    try:
        data = response.json()
        error_code = data.get("code") or data.get("error")
        message = data.get("message") or data.get("error_description") or str(data)
    except json.JSONDecodeError:
        error_code = None
        message = response.text or f"HTTP {status_code}"

    logger.warning("HTTP error %d: %s (error_code=%s)", status_code, message, error_code)

    if status_code == HTTPStatus.UNAUTHORIZED:
        raise ChzzkAPIError(message, status_code=HTTPStatus.UNAUTHORIZED, error_code=error_code)

    if status_code == HTTPStatus.FORBIDDEN:
        raise ForbiddenError(message)

    if status_code == HTTPStatus.NOT_FOUND:
        raise NotFoundError(message)

    if status_code == HTTPStatus.TOO_MANY_REQUESTS:
        raise RateLimitError(message)

    if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise ServerError(message)

    raise ChzzkAPIError(message, status_code=status_code, error_code=error_code)


class BaseUnofficialHTTPClient[ClientT: (httpx.Client, httpx.AsyncClient)]:
    """Base class for unofficial HTTP clients with shared configuration logic."""

    _client: ClientT
    _auth: NaverCookieAuth | None

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
        self._timeout = timeout
        self._headers = self._build_headers(headers)

    def _build_headers(self, headers: Mapping[str, str] | None = None) -> dict[str, str]:
        """Build default headers with optional overrides.

        Args:
            headers: Additional headers to include.

        Returns:
            Dict of headers for requests.
        """
        default_headers = {
            "User-Agent": UNOFFICIAL_USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://chzzk.naver.com/",
            "Origin": "https://chzzk.naver.com",
        }
        if headers:
            default_headers.update(headers)
        return default_headers

    def _get_cookies(self) -> dict[str, str]:
        """Get cookies from auth if available."""
        if self._auth:
            return self._auth.get_cookies()
        return {}
