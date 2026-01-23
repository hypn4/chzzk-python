"""Restriction API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.constants import Defaults
from chzzk.http import RESTRICT_CHANNELS_URL
from chzzk.models.restriction import RestrictedChannel


class RestrictionService(BaseService):
    """Synchronous Restriction API service.

    Provides access to restriction-related API endpoints.
    """

    def get_list(
        self,
        *,
        size: int = Defaults.PAGE_SIZE,
        next_token: str | None = None,
    ) -> list[RestrictedChannel]:
        """Get the list of restricted channels.

        Args:
            size: Number of results per page.
            next_token: Pagination token for the next page.

        Returns:
            List of RestrictedChannel objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params: dict[str, str | int] = {"size": size}
        if next_token:
            params["next"] = next_token

        data = self._http.get(
            RESTRICT_CHANNELS_URL,
            params=params,
            headers=self._get_token_headers(),
        )
        channels = data.get("data", [])
        return [RestrictedChannel.model_validate(item) for item in channels]

    def add(self, target_channel_id: str) -> None:
        """Add a channel to the restriction list.

        Args:
            target_channel_id: The channel ID to restrict.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            RESTRICT_CHANNELS_URL,
            json={"targetChannelId": target_channel_id},
            headers=self._get_token_headers(),
        )

    def remove(self, target_channel_id: str) -> None:
        """Remove a channel from the restriction list.

        Args:
            target_channel_id: The channel ID to unrestrict.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.delete(
            RESTRICT_CHANNELS_URL,
            json={"targetChannelId": target_channel_id},
            headers=self._get_token_headers(),
        )


class AsyncRestrictionService(AsyncBaseService):
    """Asynchronous Restriction API service.

    Provides access to restriction-related API endpoints.
    """

    async def get_list(
        self,
        *,
        size: int = Defaults.PAGE_SIZE,
        next_token: str | None = None,
    ) -> list[RestrictedChannel]:
        """Get the list of restricted channels.

        Args:
            size: Number of results per page.
            next_token: Pagination token for the next page.

        Returns:
            List of RestrictedChannel objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params: dict[str, str | int] = {"size": size}
        if next_token:
            params["next"] = next_token

        data = await self._http.get(
            RESTRICT_CHANNELS_URL,
            params=params,
            headers=await self._get_token_headers(),
        )
        channels = data.get("data", [])
        return [RestrictedChannel.model_validate(item) for item in channels]

    async def add(self, target_channel_id: str) -> None:
        """Add a channel to the restriction list.

        Args:
            target_channel_id: The channel ID to restrict.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            RESTRICT_CHANNELS_URL,
            json={"targetChannelId": target_channel_id},
            headers=await self._get_token_headers(),
        )

    async def remove(self, target_channel_id: str) -> None:
        """Remove a channel from the restriction list.

        Args:
            target_channel_id: The channel ID to unrestrict.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.delete(
            RESTRICT_CHANNELS_URL,
            json={"targetChannelId": target_channel_id},
            headers=await self._get_token_headers(),
        )
