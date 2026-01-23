"""Custom exception classes for Chzzk SDK."""

from __future__ import annotations


class ChzzkError(Exception):
    """Base exception for all Chzzk SDK errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ChzzkAPIError(ChzzkError):
    """Exception raised when Chzzk API returns an error response.

    Attributes:
        status_code: HTTP status code from the response.
        error_code: Error code from Chzzk API (e.g., "INVALID_TOKEN").
        message: Human-readable error message.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.status_code}] {self.error_code}: {self.message}"
        return f"[{self.status_code}] {self.message}"


class AuthenticationError(ChzzkAPIError):
    """Exception raised for authentication failures (401 errors)."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str | None = None,
    ) -> None:
        super().__init__(message, status_code=401, error_code=error_code)


class InvalidClientError(AuthenticationError):
    """Exception raised when client credentials are invalid."""

    def __init__(self, message: str = "Invalid client credentials") -> None:
        super().__init__(message, error_code="INVALID_CLIENT")


class InvalidTokenError(AuthenticationError):
    """Exception raised when access token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message, error_code="INVALID_TOKEN")


class ForbiddenError(ChzzkAPIError):
    """Exception raised when access is forbidden (403 errors)."""

    def __init__(self, message: str = "Access forbidden") -> None:
        super().__init__(message, status_code=403, error_code="FORBIDDEN")


class NotFoundError(ChzzkAPIError):
    """Exception raised when resource is not found (404 errors)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class RateLimitError(ChzzkAPIError):
    """Exception raised when rate limit is exceeded (429 errors)."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, status_code=429, error_code="TOO_MANY_REQUESTS")


class ServerError(ChzzkAPIError):
    """Exception raised for server-side errors (5xx errors)."""

    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message, status_code=500, error_code="INTERNAL_SERVER_ERROR")


class TokenExpiredError(ChzzkError):
    """Exception raised when both access token and refresh token are expired."""

    def __init__(self, message: str = "Token expired, re-authentication required") -> None:
        super().__init__(message)


class InvalidStateError(ChzzkError):
    """Exception raised when OAuth state parameter doesn't match."""

    def __init__(self, message: str = "Invalid state parameter") -> None:
        super().__init__(message)


class SessionError(ChzzkError):
    """Base exception for session-related errors."""

    pass


class SessionConnectionError(SessionError):
    """Exception raised when Socket.IO connection fails."""

    def __init__(self, message: str = "Failed to connect to session") -> None:
        super().__init__(message)


class SessionLimitExceededError(SessionError):
    """Exception raised when maximum session limit is exceeded."""

    def __init__(self, message: str = "Maximum session limit exceeded") -> None:
        super().__init__(message)


class EventSubscriptionError(SessionError):
    """Exception raised when event subscription fails."""

    def __init__(self, message: str = "Failed to subscribe to event") -> None:
        super().__init__(message)


# Unofficial API Errors


class UnofficialAPIError(ChzzkError):
    """Base exception for unofficial Chzzk API errors."""

    pass


class CookieAuthenticationError(UnofficialAPIError):
    """Exception raised when cookie authentication fails or is missing."""

    def __init__(self, message: str = "Cookie authentication required") -> None:
        super().__init__(message)


class ChatConnectionError(UnofficialAPIError):
    """Exception raised when chat WebSocket connection fails."""

    def __init__(self, message: str = "Failed to connect to chat") -> None:
        super().__init__(message)


class ChatNotLiveError(UnofficialAPIError):
    """Exception raised when trying to connect to chat for a non-live channel."""

    def __init__(self, message: str = "Channel is not currently live") -> None:
        super().__init__(message)


class ChatReconnectError(UnofficialAPIError):
    """Exception raised when chat reconnection fails after maximum attempts.

    Attributes:
        attempt: The number of reconnection attempts made.
        max_attempts: The maximum number of attempts allowed.
    """

    def __init__(
        self,
        message: str = "Chat reconnection failed",
        attempt: int = 0,
        max_attempts: int = 0,
    ) -> None:
        self.attempt = attempt
        self.max_attempts = max_attempts
        super().__init__(message)
