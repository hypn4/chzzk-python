"""API endpoints for unofficial Chzzk API."""

# Base URLs for unofficial APIs
CHZZK_API_BASE_URL = "https://api.chzzk.naver.com"
GAME_API_BASE_URL = "https://comm-api.game.naver.com"

# Live detail endpoint (for getting chatChannelId)
LIVE_DETAIL_URL = f"{CHZZK_API_BASE_URL}/service/v3/channels/{{channel_id}}/live-detail"

# Chat access token endpoint
CHAT_ACCESS_TOKEN_URL = f"{GAME_API_BASE_URL}/nng_main/v1/chats/access-token"

# User status endpoint (for getting userIdHash)
USER_STATUS_URL = f"{GAME_API_BASE_URL}/nng_main/v1/user/getUserStatus"

# Chat profile endpoint
CHAT_PROFILE_URL = (
    f"{GAME_API_BASE_URL}/nng_main/v1/chats/{{chat_channel_id}}/users/{{user_id}}/profile"
)


def live_detail_url(channel_id: str) -> str:
    """Get URL for live detail API.

    Args:
        channel_id: Channel ID to get live detail for.

    Returns:
        Formatted URL string.
    """
    return LIVE_DETAIL_URL.format(channel_id=channel_id)


def chat_access_token_url() -> str:
    """Get URL for chat access token API.

    Returns:
        URL string.
    """
    return CHAT_ACCESS_TOKEN_URL


def chat_profile_url(chat_channel_id: str, user_id: str) -> str:
    """Get URL for chat profile API.

    Args:
        chat_channel_id: Chat channel ID.
        user_id: User ID.

    Returns:
        Formatted URL string.
    """
    return CHAT_PROFILE_URL.format(chat_channel_id=chat_channel_id, user_id=user_id)


def user_status_url() -> str:
    """Get URL for user status API.

    Returns:
        URL string.
    """
    return USER_STATUS_URL
