"""Exception classes for Chzzk SDK."""

from chzzk.exceptions.errors import (
    AuthenticationError,
    ChzzkAPIError,
    ChzzkError,
    EventSubscriptionError,
    ForbiddenError,
    InvalidClientError,
    InvalidStateError,
    InvalidTokenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    SessionConnectionError,
    SessionError,
    SessionLimitExceededError,
    TokenExpiredError,
)

__all__ = [
    "AuthenticationError",
    "ChzzkAPIError",
    "ChzzkError",
    "EventSubscriptionError",
    "ForbiddenError",
    "InvalidClientError",
    "InvalidStateError",
    "InvalidTokenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "SessionConnectionError",
    "SessionError",
    "SessionLimitExceededError",
    "TokenExpiredError",
]
