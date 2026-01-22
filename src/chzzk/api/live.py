"""Live API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.http import LIVE_SETTING_URL, LIVES_URL, STREAM_KEY_URL
from chzzk.models.common import CategoryType
from chzzk.models.live import (
    LiveInfo,
    LiveListResponse,
    LiveSetting,
    StreamKey,
    UpdateLiveSettingRequest,
)


class LiveService(BaseService):
    """Synchronous Live API service.

    Provides access to live broadcast-related API endpoints.
    """

    def get_lives(
        self,
        *,
        size: int = 20,
        next_token: str | None = None,
    ) -> LiveListResponse:
        """Get a list of live broadcasts.

        Args:
            size: Number of results per page.
            next_token: Pagination token for the next page.

        Returns:
            LiveListResponse containing list of LiveInfo and pagination info.

        Raises:
            ChzzkAPIError: If the API request fails.
        """
        params: dict[str, str | int] = {"size": size}
        if next_token:
            params["next"] = next_token

        data = self._http.get(
            LIVES_URL,
            params=params,
            headers=self._get_client_headers(),
        )

        lives = [LiveInfo.model_validate(item) for item in data.get("data", [])]
        page_data = data.get("page", {})
        from chzzk.models.common import Page

        return LiveListResponse(data=lives, page=Page.model_validate(page_data))

    def get_stream_key(self) -> StreamKey:
        """Get the stream key for the authenticated user's channel.

        Returns:
            StreamKey object containing the stream key.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(STREAM_KEY_URL, headers=self._get_token_headers())
        return StreamKey.model_validate(data)

    def get_setting(self) -> LiveSetting:
        """Get the live broadcast setting for the authenticated user's channel.

        Returns:
            LiveSetting object containing the broadcast settings.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(LIVE_SETTING_URL, headers=self._get_token_headers())
        return LiveSetting.model_validate(data)

    def update_setting(
        self,
        *,
        default_live_title: str | None = None,
        category_type: CategoryType | None = None,
        category_id: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Update the live broadcast setting.

        Args:
            default_live_title: Default title for the broadcast.
            category_type: Category type.
            category_id: Category ID.
            tags: List of tags for the broadcast.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        request = UpdateLiveSettingRequest(
            default_live_title=default_live_title,
            category_type=category_type,
            category_id=category_id,
            tags=tags,
        )
        self._http.patch(
            LIVE_SETTING_URL,
            json=request.model_dump(by_alias=True, exclude_none=True),
            headers=self._get_token_headers(),
        )


class AsyncLiveService(AsyncBaseService):
    """Asynchronous Live API service.

    Provides access to live broadcast-related API endpoints.
    """

    async def get_lives(
        self,
        *,
        size: int = 20,
        next_token: str | None = None,
    ) -> LiveListResponse:
        """Get a list of live broadcasts.

        Args:
            size: Number of results per page.
            next_token: Pagination token for the next page.

        Returns:
            LiveListResponse containing list of LiveInfo and pagination info.

        Raises:
            ChzzkAPIError: If the API request fails.
        """
        params: dict[str, str | int] = {"size": size}
        if next_token:
            params["next"] = next_token

        data = await self._http.get(
            LIVES_URL,
            params=params,
            headers=self._get_client_headers(),
        )

        lives = [LiveInfo.model_validate(item) for item in data.get("data", [])]
        page_data = data.get("page", {})
        from chzzk.models.common import Page

        return LiveListResponse(data=lives, page=Page.model_validate(page_data))

    async def get_stream_key(self) -> StreamKey:
        """Get the stream key for the authenticated user's channel.

        Returns:
            StreamKey object containing the stream key.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(STREAM_KEY_URL, headers=await self._get_token_headers())
        return StreamKey.model_validate(data)

    async def get_setting(self) -> LiveSetting:
        """Get the live broadcast setting for the authenticated user's channel.

        Returns:
            LiveSetting object containing the broadcast settings.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(LIVE_SETTING_URL, headers=await self._get_token_headers())
        return LiveSetting.model_validate(data)

    async def update_setting(
        self,
        *,
        default_live_title: str | None = None,
        category_type: CategoryType | None = None,
        category_id: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Update the live broadcast setting.

        Args:
            default_live_title: Default title for the broadcast.
            category_type: Category type.
            category_id: Category ID.
            tags: List of tags for the broadcast.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        request = UpdateLiveSettingRequest(
            default_live_title=default_live_title,
            category_type=category_type,
            category_id=category_id,
            tags=tags,
        )
        await self._http.patch(
            LIVE_SETTING_URL,
            json=request.model_dump(by_alias=True, exclude_none=True),
            headers=await self._get_token_headers(),
        )
