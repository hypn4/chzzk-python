"""Exception classes for Chzzk SDK."""

from chzzk.exceptions.errors import (
    AuthenticationError,
    ChzzkAPIError,
    ChzzkError,
    ForbiddenError,
    InvalidClientError,
    InvalidStateError,
    InvalidTokenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TokenExpiredError,
)

__all__ = [
    "AuthenticationError",
    "ChzzkAPIError",
    "ChzzkError",
    "ForbiddenError",
    "InvalidClientError",
    "InvalidStateError",
    "InvalidTokenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TokenExpiredError",
]
