"""Live detail service for unofficial Chzzk API."""

from __future__ import annotations

from chzzk.unofficial.api.base import AsyncUnofficialBaseService, UnofficialBaseService
from chzzk.unofficial.http.endpoints import live_detail_url
from chzzk.unofficial.models.live import LiveDetail


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
