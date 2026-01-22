"""Token storage implementations for Chzzk OAuth."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from chzzk.auth.models import Token

if TYPE_CHECKING:
    pass


class FileTokenStorage:
    """File-based token storage implementation.

    Stores tokens as JSON in a local file. Useful for CLI applications
    or simple server applications that need persistent token storage.

    Example:
        >>> storage = FileTokenStorage(".chzzk_token.json")
        >>> oauth = ChzzkOAuth(
        ...     client_id="...",
        ...     client_secret="...",
        ...     redirect_uri="...",
        ...     token_storage=storage,
        ... )
    """

    def __init__(self, file_path: str | Path) -> None:
        """Initialize file-based token storage.

        Args:
            file_path: Path to the token storage file.
        """
        self._file_path = Path(file_path)

    def get_token(self) -> Token | None:
        """Retrieve the stored token from file."""
        if not self._file_path.exists():
            return None

        try:
            data = json.loads(self._file_path.read_text(encoding="utf-8"))
            return Token.model_validate(data)
        except (json.JSONDecodeError, OSError):
            return None

    def save_token(self, token: Token) -> None:
        """Save a token to file."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_path.write_text(
            token.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def delete_token(self) -> None:
        """Delete the stored token file."""
        if self._file_path.exists():
            self._file_path.unlink()


class CallbackTokenStorage:
    """Callback-based token storage implementation.

    Allows integration with external storage systems like databases
    or Redis by providing custom callback functions.

    Example:
        >>> async def load_from_db(user_id: str) -> Token | None:
        ...     # Load token from database
        ...     pass
        ...
        >>> async def save_to_db(user_id: str, token: Token) -> None:
        ...     # Save token to database
        ...     pass
        ...
        >>> async def delete_from_db(user_id: str) -> None:
        ...     # Delete token from database
        ...     pass
        ...
        >>> storage = CallbackTokenStorage(
        ...     get_callback=lambda: load_from_db("user123"),
        ...     save_callback=lambda t: save_to_db("user123", t),
        ...     delete_callback=lambda: delete_from_db("user123"),
        ... )
    """

    def __init__(
        self,
        *,
        get_callback: Callable[[], Token | None],
        save_callback: Callable[[Token], None],
        delete_callback: Callable[[], None],
    ) -> None:
        """Initialize callback-based token storage.

        Args:
            get_callback: Function to retrieve the stored token.
            save_callback: Function to save a token.
            delete_callback: Function to delete the stored token.
        """
        self._get_callback = get_callback
        self._save_callback = save_callback
        self._delete_callback = delete_callback

    def get_token(self) -> Token | None:
        """Retrieve the stored token via callback."""
        return self._get_callback()

    def save_token(self, token: Token) -> None:
        """Save a token via callback."""
        self._save_callback(token)

    def delete_token(self) -> None:
        """Delete the stored token via callback."""
        self._delete_callback()
