"""Unified Chzzk API client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chzzk.api.category import AsyncCategoryService, CategoryService
from chzzk.api.channel import AsyncChannelService, ChannelService
from chzzk.api.chat import AsyncChatService, ChatService
from chzzk.api.live import AsyncLiveService, LiveService
from chzzk.api.restriction import AsyncRestrictionService, RestrictionService
from chzzk.api.session import AsyncSessionService, SessionService
from chzzk.api.user import AsyncUserService, UserService
from chzzk.auth.oauth import AsyncChzzkOAuth, ChzzkOAuth, TokenStorage
from chzzk.http.client import AsyncHTTPClient, HTTPClient
from chzzk.realtime import AsyncChzzkEventClient, ChzzkEventClient

if TYPE_CHECKING:
    from chzzk.auth.models import Token


class ChzzkClient:
    """Synchronous Chzzk API client.

    Provides unified access to all Chzzk API services with integrated OAuth support.

    Example (with OAuth):
        >>> client = ChzzkClient(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     redirect_uri="http://localhost:8080/callback",
        ... )
        >>> auth_url, state = client.get_authorization_url()
        >>> # User visits auth_url and gets redirected back with code
        >>> token = client.authenticate(code, state)
        >>> user = client.user.get_me()

    Example (with direct token):
        >>> client = ChzzkClient(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     access_token="your-access-token",
        ... )
        >>> user = client.user.get_me()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        redirect_uri: str | None = None,
        access_token: str | None = None,
        token_storage: TokenStorage | None = None,
        auto_refresh: bool = True,
    ) -> None:
        """Initialize the Chzzk client.

        Args:
            client_id: Your Chzzk application's client ID.
            client_secret: Your Chzzk application's client secret.
            redirect_uri: OAuth redirect URI. Required for OAuth flow.
            access_token: Optional access token for user-authenticated requests.
            token_storage: Optional custom token storage for OAuth.
            auto_refresh: Whether to automatically refresh expired tokens.
        """
        self._http = HTTPClient()
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._auto_refresh = auto_refresh

        # Initialize OAuth client if redirect_uri is provided
        self._oauth: ChzzkOAuth | None = None
        if redirect_uri:
            self._oauth = ChzzkOAuth(
                client_id,
                client_secret,
                redirect_uri,
                token_storage=token_storage,
            )

        self._init_services()

    def _init_services(self) -> None:
        """Initialize all API services."""
        common_kwargs = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "access_token": self._access_token,
            "token_refresher": self._create_token_refresher(),
        }

        self.user = UserService(self._http, **common_kwargs)
        self.channel = ChannelService(self._http, **common_kwargs)
        self.category = CategoryService(self._http, **common_kwargs)
        self.live = LiveService(self._http, **common_kwargs)
        self.chat = ChatService(self._http, **common_kwargs)
        self.restriction = RestrictionService(self._http, **common_kwargs)
        self.session = SessionService(self._http, **common_kwargs)

    def _create_token_refresher(self):
        """Create a token refresher callback for automatic token refresh."""
        if not self._oauth or not self._auto_refresh:
            return None

        def refresher() -> str | None:
            if not self._oauth:
                return self._access_token

            token = self._oauth.get_token()
            if token is None:
                return self._access_token

            if token.is_expired:
                token = self._oauth.refresh_token()
                self._access_token = token.access_token

            return token.access_token

        return refresher

    # OAuth methods

    def get_authorization_url(self, *, state: str | None = None) -> tuple[str, str]:
        """Generate the authorization URL for user authentication.

        Args:
            state: Optional state parameter. If not provided, a random one is generated.

        Returns:
            A tuple of (authorization_url, state).

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")
        return self._oauth.get_authorization_url(state=state)

    def authenticate(
        self,
        code: str,
        state: str,
        *,
        validate_state: bool = True,
    ) -> Token:
        """Exchange an authorization code for access and refresh tokens.

        This method handles the OAuth callback, exchanges the code for tokens,
        and automatically configures all services with the new access token.

        Args:
            code: The authorization code received from the callback.
            state: The state parameter received from the callback.
            validate_state: Whether to validate the state parameter.

        Returns:
            The Token object containing access and refresh tokens.

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
            InvalidStateError: If state validation fails.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")

        token = self._oauth.exchange_code(code, state, validate_state=validate_state)
        self.set_access_token(token.access_token)
        return token

    def refresh_token(self, refresh_token: str | None = None) -> Token:
        """Refresh the access token.

        Args:
            refresh_token: Optional refresh token. If not provided,
                uses the stored token's refresh token.

        Returns:
            The new Token object.

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
            TokenExpiredError: If no refresh token is available.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")

        token = self._oauth.refresh_token(refresh_token)
        self.set_access_token(token.access_token)
        return token

    def revoke_token(self) -> None:
        """Revoke the current token.

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")

        self._oauth.revoke_token()
        self._access_token = None

    def get_token(self) -> Token | None:
        """Get the currently stored token.

        Returns:
            The stored Token object or None.
        """
        if not self._oauth:
            return None
        return self._oauth.get_token()

    @property
    def is_authenticated(self) -> bool:
        """Check if the client has a valid access token."""
        if self._access_token:
            return True
        if self._oauth:
            token = self._oauth.get_token()
            return token is not None and not token.is_expired
        return False

    def set_access_token(self, token: str) -> None:
        """Update the access token for all services.

        Args:
            token: New access token.
        """
        self._access_token = token
        self.user.set_access_token(token)
        self.channel.set_access_token(token)
        self.category.set_access_token(token)
        self.live.set_access_token(token)
        self.chat.set_access_token(token)
        self.restriction.set_access_token(token)
        self.session.set_access_token(token)

    def create_event_client(self) -> ChzzkEventClient:
        """Create a realtime event client for receiving WebSocket events.

        Returns:
            ChzzkEventClient instance for receiving chat, donation, and subscription events.

        Example:
            >>> event_client = client.create_event_client()
            >>> @event_client.on_chat
            ... def handle_chat(event):
            ...     print(f"{event.profile.nickname}: {event.content}")
            >>> event_client.connect()
            >>> event_client.subscribe_chat()
            >>> event_client.run_forever()
        """
        return ChzzkEventClient(self.session)

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()
        if self._oauth:
            self._oauth.close()

    def __enter__(self) -> ChzzkClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncChzzkClient:
    """Asynchronous Chzzk API client.

    Provides unified access to all Chzzk API services with integrated OAuth support.

    Example (with OAuth):
        >>> async with AsyncChzzkClient(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     redirect_uri="http://localhost:8080/callback",
        ... ) as client:
        ...     auth_url, state = client.get_authorization_url()
        ...     # User visits auth_url and gets redirected back with code
        ...     token = await client.authenticate(code, state)
        ...     user = await client.user.get_me()

    Example (with direct token):
        >>> async with AsyncChzzkClient(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     access_token="your-access-token",
        ... ) as client:
        ...     user = await client.user.get_me()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        redirect_uri: str | None = None,
        access_token: str | None = None,
        token_storage: TokenStorage | None = None,
        auto_refresh: bool = True,
    ) -> None:
        """Initialize the async Chzzk client.

        Args:
            client_id: Your Chzzk application's client ID.
            client_secret: Your Chzzk application's client secret.
            redirect_uri: OAuth redirect URI. Required for OAuth flow.
            access_token: Optional access token for user-authenticated requests.
            token_storage: Optional custom token storage for OAuth.
            auto_refresh: Whether to automatically refresh expired tokens.
        """
        self._http = AsyncHTTPClient()
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._auto_refresh = auto_refresh

        # Initialize OAuth client if redirect_uri is provided
        self._oauth: AsyncChzzkOAuth | None = None
        if redirect_uri:
            self._oauth = AsyncChzzkOAuth(
                client_id,
                client_secret,
                redirect_uri,
                token_storage=token_storage,
            )

        self._init_services()

    def _init_services(self) -> None:
        """Initialize all API services."""
        common_kwargs = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "access_token": self._access_token,
            "async_token_refresher": self._create_async_token_refresher(),
        }

        self.user = AsyncUserService(self._http, **common_kwargs)
        self.channel = AsyncChannelService(self._http, **common_kwargs)
        self.category = AsyncCategoryService(self._http, **common_kwargs)
        self.live = AsyncLiveService(self._http, **common_kwargs)
        self.chat = AsyncChatService(self._http, **common_kwargs)
        self.restriction = AsyncRestrictionService(self._http, **common_kwargs)
        self.session = AsyncSessionService(self._http, **common_kwargs)

    def _create_async_token_refresher(self):
        """Create an async token refresher callback for automatic token refresh."""
        if not self._oauth or not self._auto_refresh:
            return None

        async def refresher() -> str | None:
            if not self._oauth:
                return self._access_token

            token = self._oauth.get_token()
            if token is None:
                return self._access_token

            if token.is_expired:
                token = await self._oauth.refresh_token()
                self._access_token = token.access_token

            return token.access_token

        return refresher

    # OAuth methods

    def get_authorization_url(self, *, state: str | None = None) -> tuple[str, str]:
        """Generate the authorization URL for user authentication.

        Args:
            state: Optional state parameter. If not provided, a random one is generated.

        Returns:
            A tuple of (authorization_url, state).

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")
        return self._oauth.get_authorization_url(state=state)

    async def authenticate(
        self,
        code: str,
        state: str,
        *,
        validate_state: bool = True,
    ) -> Token:
        """Exchange an authorization code for access and refresh tokens.

        This method handles the OAuth callback, exchanges the code for tokens,
        and automatically configures all services with the new access token.

        Args:
            code: The authorization code received from the callback.
            state: The state parameter received from the callback.
            validate_state: Whether to validate the state parameter.

        Returns:
            The Token object containing access and refresh tokens.

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
            InvalidStateError: If state validation fails.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")

        token = await self._oauth.exchange_code(code, state, validate_state=validate_state)
        self.set_access_token(token.access_token)
        return token

    async def refresh_token(self, refresh_token: str | None = None) -> Token:
        """Refresh the access token.

        Args:
            refresh_token: Optional refresh token. If not provided,
                uses the stored token's refresh token.

        Returns:
            The new Token object.

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
            TokenExpiredError: If no refresh token is available.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")

        token = await self._oauth.refresh_token(refresh_token)
        self.set_access_token(token.access_token)
        return token

    async def revoke_token(self) -> None:
        """Revoke the current token.

        Raises:
            ValueError: If redirect_uri was not provided during initialization.
        """
        if not self._oauth:
            raise ValueError("redirect_uri is required for OAuth operations")

        await self._oauth.revoke_token()
        self._access_token = None

    def get_token(self) -> Token | None:
        """Get the currently stored token.

        Returns:
            The stored Token object or None.
        """
        if not self._oauth:
            return None
        return self._oauth.get_token()

    @property
    def is_authenticated(self) -> bool:
        """Check if the client has a valid access token."""
        if self._access_token:
            return True
        if self._oauth:
            token = self._oauth.get_token()
            return token is not None and not token.is_expired
        return False

    def set_access_token(self, token: str) -> None:
        """Update the access token for all services.

        Args:
            token: New access token.
        """
        self._access_token = token
        self.user.set_access_token(token)
        self.channel.set_access_token(token)
        self.category.set_access_token(token)
        self.live.set_access_token(token)
        self.chat.set_access_token(token)
        self.restriction.set_access_token(token)
        self.session.set_access_token(token)

    def create_event_client(self) -> AsyncChzzkEventClient:
        """Create a realtime event client for receiving WebSocket events.

        Returns:
            AsyncChzzkEventClient instance for receiving chat, donation, and subscription events.

        Example:
            >>> event_client = client.create_event_client()
            >>> @event_client.on_chat
            ... async def handle_chat(event):
            ...     print(f"{event.profile.nickname}: {event.content}")
            >>> await event_client.connect()
            >>> await event_client.subscribe_chat()
            >>> await event_client.run_forever()
        """
        return AsyncChzzkEventClient(self.session)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.close()
        if self._oauth:
            await self._oauth.close()

    async def __aenter__(self) -> AsyncChzzkClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
