"""Live detail service for unofficial Chzzk API."""

from __future__ import annotations

from chzzk.unofficial.api.base import AsyncUnofficialBaseService, UnofficialBaseService
from chzzk.unofficial.http.endpoints import live_detail_url, live_status_polling_url
from chzzk.unofficial.models.live import LiveDetail, LiveStatusPolling


class LiveDetailService(UnofficialBaseService):
    """Service for getting live detail information.

    This service provides access to the unofficial live detail API
    which returns additional information like chatChannelId.
    """

    def get_live_detail(self, channel_id: str) -> LiveDetail:
        """Get live detail for a channel.

        Args:
            channel_id: The channel ID to get live detail for.

        Returns:
            LiveDetail object containing stream information.
        """
        url = live_detail_url(channel_id)
        data = self._http.get(url)
        return LiveDetail.model_validate(data)


class AsyncLiveDetailService(AsyncUnofficialBaseService):
    """Async service for getting live detail information."""

    async def get_live_detail(self, channel_id: str) -> LiveDetail:
        """Get live detail for a channel.

        Args:
            channel_id: The channel ID to get live detail for.

        Returns:
            LiveDetail object containing stream information.
        """
        url = live_detail_url(channel_id)
        data = await self._http.get(url)
        return LiveDetail.model_validate(data)


class LiveStatusPollingService(UnofficialBaseService):
    """Service for polling live status information.

    This service provides lightweight status polling for monitoring
    channel state changes without the overhead of full live detail.
    """

    def get_live_status(self, channel_id: str) -> LiveStatusPolling:
        """Get live status for a channel.

        Args:
            channel_id: The channel ID to get status for.

        Returns:
            LiveStatusPolling object containing status information.
        """
        url = live_status_polling_url(channel_id)
        data = self._http.get(url)
        return LiveStatusPolling.model_validate(data)


class AsyncLiveStatusPollingService(AsyncUnofficialBaseService):
    """Async service for polling live status information."""

    async def get_live_status(self, channel_id: str) -> LiveStatusPolling:
        """Get live status for a channel.

        Args:
            channel_id: The channel ID to get status for.

        Returns:
            LiveStatusPolling object containing status information.
        """
        url = live_status_polling_url(channel_id)
        data = await self._http.get(url)
        return LiveStatusPolling.model_validate(data)
