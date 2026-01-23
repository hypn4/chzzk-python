"""Channel API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.constants import Defaults
from chzzk.http import (
    CHANNEL_FOLLOWERS_URL,
    CHANNEL_ROLES_URL,
    CHANNEL_SUBSCRIBERS_URL,
    CHANNELS_URL,
)
from chzzk.models.channel import (
    ChannelInfo,
    ChannelManager,
    Follower,
    Subscriber,
    SubscriberSortType,
)


class ChannelService(BaseService):
    """Synchronous Channel API service.

    Provides access to channel-related API endpoints.
    """

    def get_channels(self, channel_ids: list[str]) -> list[ChannelInfo]:
        """Get information for multiple channels.

        Args:
            channel_ids: List of channel IDs to look up (max 20).

        Returns:
            List of ChannelInfo objects.

        Raises:
            ChzzkAPIError: If the API request fails.
        """
        params = {"channelIds": ",".join(channel_ids)}
        data = self._http.get(
            CHANNELS_URL,
            params=params,
            headers=self._get_client_headers(),
        )
        channels = data.get("data", [])
        return [ChannelInfo.model_validate(item) for item in channels]

    def get_streaming_roles(self) -> list[ChannelManager]:
        """Get channel managers for the authenticated user's channel.

        Returns:
            List of ChannelManager objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(CHANNEL_ROLES_URL, headers=self._get_token_headers())
        managers = data.get("data", [])
        return [ChannelManager.model_validate(item) for item in managers]

    def get_followers(
        self,
        *,
        page: int = 0,
        size: int = Defaults.PAGE_SIZE,
    ) -> list[Follower]:
        """Get followers for the authenticated user's channel.

        Args:
            page: Page number (0-indexed).
            size: Number of results per page.

        Returns:
            List of Follower objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"page": page, "size": size}
        data = self._http.get(
            CHANNEL_FOLLOWERS_URL,
            params=params,
            headers=self._get_token_headers(),
        )
        followers = data.get("data", [])
        return [Follower.model_validate(item) for item in followers]

    def get_subscribers(
        self,
        *,
        page: int = 0,
        size: int = Defaults.PAGE_SIZE,
        sort: SubscriberSortType = SubscriberSortType.RECENT,
    ) -> list[Subscriber]:
        """Get subscribers for the authenticated user's channel.

        Args:
            page: Page number (0-indexed).
            size: Number of results per page.
            sort: Sort order (RECENT or LONGER).

        Returns:
            List of Subscriber objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"page": page, "size": size, "sortType": sort.value}
        data = self._http.get(
            CHANNEL_SUBSCRIBERS_URL,
            params=params,
            headers=self._get_token_headers(),
        )
        subscribers = data.get("data", [])
        return [Subscriber.model_validate(item) for item in subscribers]


class AsyncChannelService(AsyncBaseService):
    """Asynchronous Channel API service.

    Provides access to channel-related API endpoints.
    """

    async def get_channels(self, channel_ids: list[str]) -> list[ChannelInfo]:
        """Get information for multiple channels.

        Args:
            channel_ids: List of channel IDs to look up (max 20).

        Returns:
            List of ChannelInfo objects.

        Raises:
            ChzzkAPIError: If the API request fails.
        """
        params = {"channelIds": ",".join(channel_ids)}
        data = await self._http.get(
            CHANNELS_URL,
            params=params,
            headers=self._get_client_headers(),
        )
        channels = data.get("data", [])
        return [ChannelInfo.model_validate(item) for item in channels]

    async def get_streaming_roles(self) -> list[ChannelManager]:
        """Get channel managers for the authenticated user's channel.

        Returns:
            List of ChannelManager objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(CHANNEL_ROLES_URL, headers=await self._get_token_headers())
        managers = data.get("data", [])
        return [ChannelManager.model_validate(item) for item in managers]

    async def get_followers(
        self,
        *,
        page: int = 0,
        size: int = Defaults.PAGE_SIZE,
    ) -> list[Follower]:
        """Get followers for the authenticated user's channel.

        Args:
            page: Page number (0-indexed).
            size: Number of results per page.

        Returns:
            List of Follower objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"page": page, "size": size}
        data = await self._http.get(
            CHANNEL_FOLLOWERS_URL,
            params=params,
            headers=await self._get_token_headers(),
        )
        followers = data.get("data", [])
        return [Follower.model_validate(item) for item in followers]

    async def get_subscribers(
        self,
        *,
        page: int = 0,
        size: int = Defaults.PAGE_SIZE,
        sort: SubscriberSortType = SubscriberSortType.RECENT,
    ) -> list[Subscriber]:
        """Get subscribers for the authenticated user's channel.

        Args:
            page: Page number (0-indexed).
            size: Number of results per page.
            sort: Sort order (RECENT or LONGER).

        Returns:
            List of Subscriber objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"page": page, "size": size, "sortType": sort.value}
        data = await self._http.get(
            CHANNEL_SUBSCRIBERS_URL,
            params=params,
            headers=await self._get_token_headers(),
        )
        subscribers = data.get("data", [])
        return [Subscriber.model_validate(item) for item in subscribers]
