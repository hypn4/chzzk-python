"""Pydantic models for Chzzk OAuth authentication."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, computed_field


class GrantType(StrEnum):
    """OAuth grant type enumeration."""

    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"


class TokenTypeHint(StrEnum):
    """Token type hint for revocation."""

    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"


class TokenResponse(BaseModel):
    """Response model for token endpoint (camelCase from API)."""

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = Field(alias="tokenType")
    expires_in: int = Field(alias="expiresIn")
    scope: str | None = None

    model_config = {"populate_by_name": True}


class Token(BaseModel):
    """Token model with expiration tracking.

    This model stores the token data along with the timestamp when it was issued,
    allowing for accurate expiration checking.
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str | None = None
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}

    @computed_field
    @property
    def expires_at(self) -> datetime:
        """Calculate the expiration time of the access token."""
        return self.issued_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        """Check if the access token is expired.

        Returns True if the token has expired or will expire within 60 seconds.
        """
        buffer = timedelta(seconds=60)
        return datetime.now(UTC) >= (self.expires_at - buffer)

    @classmethod
    def from_response(cls, response: TokenResponse) -> Self:
        """Create a Token instance from a TokenResponse."""
        return cls(
            access_token=response.access_token,
            refresh_token=response.refresh_token,
            token_type=response.token_type,
            expires_in=response.expires_in,
            scope=response.scope,
        )


class AuthorizationCodeRequest(BaseModel):
    """Request model for authorization code token exchange."""

    grant_type: str = Field(default=GrantType.AUTHORIZATION_CODE, serialization_alias="grantType")
    client_id: str = Field(serialization_alias="clientId")
    client_secret: str = Field(serialization_alias="clientSecret")
    code: str
    state: str

    model_config = {"populate_by_name": True}


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    grant_type: str = Field(default=GrantType.REFRESH_TOKEN, serialization_alias="grantType")
    client_id: str = Field(serialization_alias="clientId")
    client_secret: str = Field(serialization_alias="clientSecret")
    refresh_token: str = Field(serialization_alias="refreshToken")

    model_config = {"populate_by_name": True}


class RevokeTokenRequest(BaseModel):
    """Request model for token revocation."""

    client_id: str = Field(serialization_alias="clientId")
    client_secret: str = Field(serialization_alias="clientSecret")
    token: str
    token_type_hint: str = Field(
        default=TokenTypeHint.ACCESS_TOKEN,
        serialization_alias="tokenTypeHint",
    )

    model_config = {"populate_by_name": True}
