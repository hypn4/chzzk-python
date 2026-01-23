"""Constants used across the Chzzk SDK."""

from __future__ import annotations

try:
    from chzzk._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

# User agent for official API requests
USER_AGENT = f"chzzk-python/{__version__}"

# User agent for unofficial API (browser-like)
UNOFFICIAL_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Default HTTP timeout in seconds
DEFAULT_TIMEOUT = 30.0


class HTTPStatus:
    """HTTP status codes used in error handling."""

    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500


class WSProtocol:
    """WebSocket protocol constants for chat."""

    DEV_TYPE = 2001
    MSG_TYPE_CODE = 1
    RECENT_MESSAGE_COUNT = 50
    TID_CONNECT = 1
    TID_SEND = 2
    TID_RECENT = 3
    SERVICE_ID = "game"
    PROTOCOL_VERSION = "3"


class WSConfig:
    """WebSocket configuration constants."""

    PING_INTERVAL = 20
    PING_TIMEOUT = 10
    CONNECTION_TIMEOUT = 10.0


class StatusText:
    """Status display text for CLI."""

    LIVE = "LIVE"
    OFFLINE = "OFFLINE"


class ChatAuthMode:
    """Chat authentication modes."""

    SEND = "SEND"
    READ = "READ"


class ChatExtra:
    """Chat message extra field values."""

    CHAT_TYPE_STREAMING = "STREAMING"
    OS_TYPE_PC = "PC"


class Defaults:
    """Default configuration values."""

    PAGE_SIZE = 20
    TOKEN_EXPIRY_BUFFER_SECONDS = 60
