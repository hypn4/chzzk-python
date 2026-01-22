"""API endpoints and base URLs for Chzzk API."""

# Base URLs
CHZZK_BASE_URL = "https://chzzk.naver.com"
OPENAPI_BASE_URL = "https://openapi.chzzk.naver.com"

# Authorization endpoints
AUTH_INTERLOCK_URL = f"{CHZZK_BASE_URL}/account-interlock"
AUTH_TOKEN_URL = f"{OPENAPI_BASE_URL}/auth/v1/token"
AUTH_REVOKE_URL = f"{OPENAPI_BASE_URL}/auth/v1/token/revoke"

# Open API prefix
OPEN_API_PREFIX = f"{OPENAPI_BASE_URL}/open/v1"

# User endpoints
USER_ME_URL = f"{OPEN_API_PREFIX}/users/me"

# Channel endpoints
CHANNELS_URL = f"{OPEN_API_PREFIX}/channels"
CHANNEL_ROLES_URL = f"{OPEN_API_PREFIX}/channels/streaming-roles"
CHANNEL_FOLLOWERS_URL = f"{OPEN_API_PREFIX}/channels/followers"
CHANNEL_SUBSCRIBERS_URL = f"{OPEN_API_PREFIX}/channels/subscribers"

# Category endpoints
CATEGORIES_SEARCH_URL = f"{OPEN_API_PREFIX}/categories/search"

# Live endpoints
LIVES_URL = f"{OPEN_API_PREFIX}/lives"
STREAM_KEY_URL = f"{OPEN_API_PREFIX}/streams/key"
LIVE_SETTING_URL = f"{OPEN_API_PREFIX}/lives/setting"

# Chat endpoints
CHAT_SEND_URL = f"{OPEN_API_PREFIX}/chats/send"
CHAT_NOTICE_URL = f"{OPEN_API_PREFIX}/chats/notice"
CHAT_SETTINGS_URL = f"{OPEN_API_PREFIX}/chats/settings"

# Restriction endpoints
RESTRICT_CHANNELS_URL = f"{OPEN_API_PREFIX}/restrict-channels"

# Session endpoints
SESSIONS_AUTH_URL = f"{OPEN_API_PREFIX}/sessions/auth"
SESSIONS_AUTH_CLIENT_URL = f"{OPEN_API_PREFIX}/sessions/auth/client"
SESSIONS_URL = f"{OPEN_API_PREFIX}/sessions"
SESSIONS_CLIENT_URL = f"{OPEN_API_PREFIX}/sessions/client"
SESSIONS_SUBSCRIBE_CHAT_URL = f"{OPEN_API_PREFIX}/sessions/events/subscribe/chat"
SESSIONS_SUBSCRIBE_DONATION_URL = f"{OPEN_API_PREFIX}/sessions/events/subscribe/donation"
SESSIONS_SUBSCRIBE_SUBSCRIPTION_URL = f"{OPEN_API_PREFIX}/sessions/events/subscribe/subscription"
SESSIONS_UNSUBSCRIBE_CHAT_URL = f"{OPEN_API_PREFIX}/sessions/events/unsubscribe/chat"
SESSIONS_UNSUBSCRIBE_DONATION_URL = f"{OPEN_API_PREFIX}/sessions/events/unsubscribe/donation"
SESSIONS_UNSUBSCRIBE_SUBSCRIPTION_URL = (
    f"{OPEN_API_PREFIX}/sessions/events/unsubscribe/subscription"
)
