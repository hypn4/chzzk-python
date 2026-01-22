"""API endpoints and base URLs for Chzzk API."""

# Base URLs
CHZZK_BASE_URL = "https://chzzk.naver.com"
OPENAPI_BASE_URL = "https://openapi.chzzk.naver.com"

# Authorization endpoints
AUTH_INTERLOCK_URL = f"{CHZZK_BASE_URL}/account-interlock"
AUTH_TOKEN_URL = f"{OPENAPI_BASE_URL}/auth/v1/token"
AUTH_REVOKE_URL = f"{OPENAPI_BASE_URL}/auth/v1/token/revoke"

# Open API endpoints (for future use)
OPEN_API_PREFIX = f"{OPENAPI_BASE_URL}/open/v1"
