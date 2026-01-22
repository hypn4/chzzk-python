"""Category API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.http import CATEGORIES_SEARCH_URL
from chzzk.models.category import Category


class CategoryService(BaseService):
    """Synchronous Category API service.

    Provides access to category-related API endpoints.
    """

    def search(self, query: str, *, size: int = 20) -> list[Category]:
        """Search for categories.

        Args:
            query: Search query string.
            size: Maximum number of results to return (default: 20).

        Returns:
            List of Category objects matching the query.

        Raises:
            ChzzkAPIError: If the API request fails.
        """
        params = {"query": query, "size": size}
        data = self._http.get(
            CATEGORIES_SEARCH_URL,
            params=params,
            headers=self._get_client_headers(),
        )
        categories = data.get("data", [])
        return [Category.model_validate(item) for item in categories]


class AsyncCategoryService(AsyncBaseService):
    """Asynchronous Category API service.

    Provides access to category-related API endpoints.
    """

    async def search(self, query: str, *, size: int = 20) -> list[Category]:
        """Search for categories.

        Args:
            query: Search query string.
            size: Maximum number of results to return (default: 20).

        Returns:
            List of Category objects matching the query.

        Raises:
            ChzzkAPIError: If the API request fails.
        """
        params = {"query": query, "size": size}
        data = await self._http.get(
            CATEGORIES_SEARCH_URL,
            params=params,
            headers=self._get_client_headers(),
        )
        categories = data.get("data", [])
        return [Category.model_validate(item) for item in categories]
