"""Session API service for Chzzk."""

from __future__ import annotations

from chzzk.api.base import AsyncBaseService, BaseService
from chzzk.constants import Defaults
from chzzk.http import (
    SESSIONS_AUTH_CLIENT_URL,
    SESSIONS_AUTH_URL,
    SESSIONS_CLIENT_URL,
    SESSIONS_SUBSCRIBE_CHAT_URL,
    SESSIONS_SUBSCRIBE_DONATION_URL,
    SESSIONS_SUBSCRIBE_SUBSCRIPTION_URL,
    SESSIONS_UNSUBSCRIBE_CHAT_URL,
    SESSIONS_UNSUBSCRIBE_DONATION_URL,
    SESSIONS_UNSUBSCRIBE_SUBSCRIPTION_URL,
    SESSIONS_URL,
)
from chzzk.models.session import SessionAuthResponse, SessionInfo, SessionListResponse


class SessionService(BaseService):
    """Synchronous Session API service.

    Provides access to session-related API endpoints for WebSocket event subscriptions.
    """

    def create_session(self) -> SessionAuthResponse:
        """Create a session for WebSocket connection (user authentication).

        Creates a session URL using access token authentication.
        Maximum 3 connections per user.

        Returns:
            SessionAuthResponse containing the WebSocket connection URL.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(SESSIONS_AUTH_URL, headers=self._get_token_headers())
        return SessionAuthResponse.model_validate(data)

    def create_client_session(self) -> SessionAuthResponse:
        """Create a session for WebSocket connection (client authentication).

        Creates a session URL using client credentials authentication.
        Maximum 10 connections per client.

        Returns:
            SessionAuthResponse containing the WebSocket connection URL.

        Raises:
            InvalidClientError: If the client credentials are invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = self._http.get(SESSIONS_AUTH_CLIENT_URL, headers=self._get_client_headers())
        return SessionAuthResponse.model_validate(data)

    def get_sessions(self, *, size: int = Defaults.PAGE_SIZE, page: int = 0) -> list[SessionInfo]:
        """Get session list (user authentication).

        Retrieves sessions created with access token authentication.

        Args:
            size: Number of sessions to retrieve (1-50). Default is 20.
            page: Page number to retrieve (0-indexed). Default is 0.

        Returns:
            List of SessionInfo objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"size": size, "page": page}
        data = self._http.get(SESSIONS_URL, params=params, headers=self._get_token_headers())
        response = SessionListResponse.model_validate(data)
        return response.data

    def get_client_sessions(
        self, *, size: int = Defaults.PAGE_SIZE, page: int = 0
    ) -> list[SessionInfo]:
        """Get session list (client authentication).

        Retrieves sessions created with client credentials authentication.

        Args:
            size: Number of sessions to retrieve (1-50). Default is 20.
            page: Page number to retrieve (0-indexed). Default is 0.

        Returns:
            List of SessionInfo objects.

        Raises:
            InvalidClientError: If the client credentials are invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"size": size, "page": page}
        headers = self._get_client_headers()
        data = self._http.get(SESSIONS_CLIENT_URL, params=params, headers=headers)
        response = SessionListResponse.model_validate(data)
        return response.data

    def subscribe_chat(self, session_key: str) -> None:
        """Subscribe to chat events for a session.

        Maximum 30 events (chat, donation, subscription) per session.

        Args:
            session_key: The session key to subscribe events to.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            SESSIONS_SUBSCRIBE_CHAT_URL,
            params={"sessionKey": session_key},
            headers=self._get_token_headers(),
        )

    def subscribe_donation(self, session_key: str) -> None:
        """Subscribe to donation events for a session.

        Maximum 30 events (chat, donation, subscription) per session.

        Args:
            session_key: The session key to subscribe events to.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            SESSIONS_SUBSCRIBE_DONATION_URL,
            params={"sessionKey": session_key},
            headers=self._get_token_headers(),
        )

    def subscribe_subscription(self, session_key: str) -> None:
        """Subscribe to subscription events for a session.

        Maximum 30 events (chat, donation, subscription) per session.

        Args:
            session_key: The session key to subscribe events to.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            SESSIONS_SUBSCRIBE_SUBSCRIPTION_URL,
            params={"sessionKey": session_key},
            headers=self._get_token_headers(),
        )

    def unsubscribe_chat(self, session_key: str) -> None:
        """Unsubscribe from chat events for a session.

        Args:
            session_key: The session key to unsubscribe events from.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            SESSIONS_UNSUBSCRIBE_CHAT_URL,
            params={"sessionKey": session_key},
            headers=self._get_token_headers(),
        )

    def unsubscribe_donation(self, session_key: str) -> None:
        """Unsubscribe from donation events for a session.

        Args:
            session_key: The session key to unsubscribe events from.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            SESSIONS_UNSUBSCRIBE_DONATION_URL,
            params={"sessionKey": session_key},
            headers=self._get_token_headers(),
        )

    def unsubscribe_subscription(self, session_key: str) -> None:
        """Unsubscribe from subscription events for a session.

        Args:
            session_key: The session key to unsubscribe events from.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        self._http.post(
            SESSIONS_UNSUBSCRIBE_SUBSCRIPTION_URL,
            params={"sessionKey": session_key},
            headers=self._get_token_headers(),
        )


class AsyncSessionService(AsyncBaseService):
    """Asynchronous Session API service.

    Provides access to session-related API endpoints for WebSocket event subscriptions.
    """

    async def create_session(self) -> SessionAuthResponse:
        """Create a session for WebSocket connection (user authentication).

        Creates a session URL using access token authentication.
        Maximum 3 connections per user.

        Returns:
            SessionAuthResponse containing the WebSocket connection URL.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(SESSIONS_AUTH_URL, headers=await self._get_token_headers())
        return SessionAuthResponse.model_validate(data)

    async def create_client_session(self) -> SessionAuthResponse:
        """Create a session for WebSocket connection (client authentication).

        Creates a session URL using client credentials authentication.
        Maximum 10 connections per client.

        Returns:
            SessionAuthResponse containing the WebSocket connection URL.

        Raises:
            InvalidClientError: If the client credentials are invalid.
            ChzzkAPIError: If the API request fails.
        """
        data = await self._http.get(SESSIONS_AUTH_CLIENT_URL, headers=self._get_client_headers())
        return SessionAuthResponse.model_validate(data)

    async def get_sessions(
        self, *, size: int = Defaults.PAGE_SIZE, page: int = 0
    ) -> list[SessionInfo]:
        """Get session list (user authentication).

        Retrieves sessions created with access token authentication.

        Args:
            size: Number of sessions to retrieve (1-50). Default is 20.
            page: Page number to retrieve (0-indexed). Default is 0.

        Returns:
            List of SessionInfo objects.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"size": size, "page": page}
        data = await self._http.get(
            SESSIONS_URL, params=params, headers=await self._get_token_headers()
        )
        response = SessionListResponse.model_validate(data)
        return response.data

    async def get_client_sessions(
        self, *, size: int = Defaults.PAGE_SIZE, page: int = 0
    ) -> list[SessionInfo]:
        """Get session list (client authentication).

        Retrieves sessions created with client credentials authentication.

        Args:
            size: Number of sessions to retrieve (1-50). Default is 20.
            page: Page number to retrieve (0-indexed). Default is 0.

        Returns:
            List of SessionInfo objects.

        Raises:
            InvalidClientError: If the client credentials are invalid.
            ChzzkAPIError: If the API request fails.
        """
        params = {"size": size, "page": page}
        data = await self._http.get(
            SESSIONS_CLIENT_URL, params=params, headers=self._get_client_headers()
        )
        response = SessionListResponse.model_validate(data)
        return response.data

    async def subscribe_chat(self, session_key: str) -> None:
        """Subscribe to chat events for a session.

        Maximum 30 events (chat, donation, subscription) per session.

        Args:
            session_key: The session key to subscribe events to.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            SESSIONS_SUBSCRIBE_CHAT_URL,
            params={"sessionKey": session_key},
            headers=await self._get_token_headers(),
        )

    async def subscribe_donation(self, session_key: str) -> None:
        """Subscribe to donation events for a session.

        Maximum 30 events (chat, donation, subscription) per session.

        Args:
            session_key: The session key to subscribe events to.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            SESSIONS_SUBSCRIBE_DONATION_URL,
            params={"sessionKey": session_key},
            headers=await self._get_token_headers(),
        )

    async def subscribe_subscription(self, session_key: str) -> None:
        """Subscribe to subscription events for a session.

        Maximum 30 events (chat, donation, subscription) per session.

        Args:
            session_key: The session key to subscribe events to.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            SESSIONS_SUBSCRIBE_SUBSCRIPTION_URL,
            params={"sessionKey": session_key},
            headers=await self._get_token_headers(),
        )

    async def unsubscribe_chat(self, session_key: str) -> None:
        """Unsubscribe from chat events for a session.

        Args:
            session_key: The session key to unsubscribe events from.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            SESSIONS_UNSUBSCRIBE_CHAT_URL,
            params={"sessionKey": session_key},
            headers=await self._get_token_headers(),
        )

    async def unsubscribe_donation(self, session_key: str) -> None:
        """Unsubscribe from donation events for a session.

        Args:
            session_key: The session key to unsubscribe events from.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            SESSIONS_UNSUBSCRIBE_DONATION_URL,
            params={"sessionKey": session_key},
            headers=await self._get_token_headers(),
        )

    async def unsubscribe_subscription(self, session_key: str) -> None:
        """Unsubscribe from subscription events for a session.

        Args:
            session_key: The session key to unsubscribe events from.

        Raises:
            InvalidTokenError: If the access token is invalid.
            ChzzkAPIError: If the API request fails.
        """
        await self._http.post(
            SESSIONS_UNSUBSCRIBE_SUBSCRIPTION_URL,
            params={"sessionKey": session_key},
            headers=await self._get_token_headers(),
        )
