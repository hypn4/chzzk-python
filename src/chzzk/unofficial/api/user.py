"""User status service for unofficial Chzzk API."""

from __future__ import annotations

from chzzk.unofficial.api.base import AsyncUnofficialBaseService, UnofficialBaseService
from chzzk.unofficial.http.endpoints import user_status_url
from chzzk.unofficial.models.user import UserStatus


class UserStatusService(UnofficialBaseService):
    """Service for getting user status.

    This service provides access to the unofficial user status API
    required for getting userIdHash for chat authentication.
    """

    def get_user_status(self) -> UserStatus:
        """Get current user status.

        Returns:
            UserStatus containing userIdHash and login status.
        """
        url = user_status_url()
        data = self._http.get(url)
        return UserStatus.model_validate(data)


class AsyncUserStatusService(AsyncUnofficialBaseService):
    """Async service for getting user status."""

    async def get_user_status(self) -> UserStatus:
        """Get current user status.

        Returns:
            UserStatus containing userIdHash and login status.
        """
        url = user_status_url()
        data = await self._http.get(url)
        return UserStatus.model_validate(data)
