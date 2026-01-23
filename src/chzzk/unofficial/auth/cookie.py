"""Cookie authentication for Naver services."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class CookieStorage(Protocol):
    """Protocol for storing and retrieving cookies."""

    def get_cookies(self) -> dict[str, str] | None:
        """Get stored cookies.

        Returns:
            Dictionary of cookies or None if not available.
        """
        ...

    def save_cookies(self, cookies: dict[str, str]) -> None:
        """Save cookies to storage.

        Args:
            cookies: Dictionary of cookies to save.
        """
        ...


class FileCookieStorage:
    """File-based cookie storage."""

    def __init__(self, file_path: str | Path) -> None:
        """Initialize file-based cookie storage.

        Args:
            file_path: Path to the cookie storage file.
        """
        self._file_path = Path(file_path)

    def get_cookies(self) -> dict[str, str] | None:
        """Get stored cookies from file.

        Returns:
            Dictionary of cookies or None if file doesn't exist.
        """
        if not self._file_path.exists():
            return None

        with self._file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_cookies(self, cookies: dict[str, str]) -> None:
        """Save cookies to file.

        Args:
            cookies: Dictionary of cookies to save.
        """
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._file_path.open("w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)


class NaverCookieAuth:
    """Naver cookie-based authentication.

    This class manages Naver session cookies (NID_AUT, NID_SES) required
    for accessing unofficial Chzzk APIs.

    Example:
        >>> auth = NaverCookieAuth(
        ...     nid_aut="your-nid-aut-cookie",
        ...     nid_ses="your-nid-ses-cookie",
        ... )
        >>> cookies = auth.get_cookies()
        >>> # Use cookies with HTTP client
    """

    COOKIE_NID_AUT = "NID_AUT"
    COOKIE_NID_SES = "NID_SES"

    def __init__(
        self,
        nid_aut: str | None = None,
        nid_ses: str | None = None,
        *,
        storage: CookieStorage | None = None,
    ) -> None:
        """Initialize Naver cookie authentication.

        Args:
            nid_aut: NID_AUT cookie value from Naver login.
            nid_ses: NID_SES cookie value from Naver login.
            storage: Optional cookie storage for persistence.
        """
        self._storage = storage
        self._cookies: dict[str, str] = {}

        # Try to load from storage first
        if storage:
            stored = storage.get_cookies()
            if stored:
                self._cookies = stored

        # Override with provided values
        if nid_aut:
            self._cookies[self.COOKIE_NID_AUT] = nid_aut
        if nid_ses:
            self._cookies[self.COOKIE_NID_SES] = nid_ses

        # Save to storage if provided
        if storage and self._cookies:
            storage.save_cookies(self._cookies)

    def get_cookies(self) -> dict[str, str]:
        """Get cookies for HTTP requests.

        Returns:
            Dictionary of cookies.
        """
        return self._cookies.copy()

    def get_cookie_header(self) -> str:
        """Get cookie header string for HTTP requests.

        Returns:
            Cookie header value in "key=value; key=value" format.
        """
        return "; ".join(f"{k}={v}" for k, v in self._cookies.items())

    def is_authenticated(self) -> bool:
        """Check if required cookies are available.

        Returns:
            True if both NID_AUT and NID_SES cookies are present.
        """
        return bool(
            self._cookies.get(self.COOKIE_NID_AUT) and self._cookies.get(self.COOKIE_NID_SES)
        )

    def update_cookies(self, nid_aut: str | None = None, nid_ses: str | None = None) -> None:
        """Update cookie values.

        Args:
            nid_aut: New NID_AUT cookie value.
            nid_ses: New NID_SES cookie value.
        """
        if nid_aut:
            self._cookies[self.COOKIE_NID_AUT] = nid_aut
        if nid_ses:
            self._cookies[self.COOKIE_NID_SES] = nid_ses

        if self._storage:
            self._storage.save_cookies(self._cookies)
