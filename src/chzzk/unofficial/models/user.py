"""User models for unofficial Chzzk API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserStatus(BaseModel):
    """User status from getUserStatus API.

    This model represents the user's authentication status and profile information
    needed for chat functionality.
    """

    has_profile: bool = Field(default=False, alias="hasProfile")
    user_id_hash: str | None = Field(default=None, alias="userIdHash")
    nickname: str | None = None
    logged_in: bool = Field(default=False, alias="loggedIn")
