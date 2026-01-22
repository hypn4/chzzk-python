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
