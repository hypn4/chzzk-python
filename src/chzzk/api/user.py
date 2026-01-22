"""User API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.http import USER_ME_URL
from chzzk.models.user import UserInfo


class UserService(BaseService):
    """Synchronous User API service.

    Provides access to user-related API endpoints.
    """

    def get_me(self) -> UserInfo:
        """Get the current authenticated user's information.

        Returns:
            UserInfo containing the user's channel ID and name.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(USER_ME_URL, headers=self._get_token_headers())
        return UserInfo.model_validate(data)


class AsyncUserService(AsyncBaseService):
    """Asynchronous User API service.

    Provides access to user-related API endpoints.
    """

    async def get_me(self) -> UserInfo:
        """Get the current authenticated user's information.

        Returns:
            UserInfo containing the user's channel ID and name.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(USER_ME_URL, headers=await self._get_token_headers())
        return UserInfo.model_validate(data)
