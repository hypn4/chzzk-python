"""Base TUI application class for Chzzk CLI."""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING, ClassVar

from textual.app import App

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager


class ChzzkApp(App):
    """Base Textual application for Chzzk CLI.

    Provides common functionality for all Chzzk TUI apps including
    configuration management and authentication cookie handling.
    """

    CSS_PATH: ClassVar[str | PurePath | list[str | PurePath] | None] = (
        Path(__file__).parent / "styles" / "app.tcss"
    )

    def __init__(
        self,
        config: ConfigManager,
        nid_aut: str | None = None,
        nid_ses: str | None = None,
    ) -> None:
        """Initialize the Chzzk TUI app.

        Args:
            config: Configuration manager instance.
            nid_aut: NID_AUT cookie value (optional, overrides stored).
            nid_ses: NID_SES cookie value (optional, overrides stored).
        """
        super().__init__()
        self.config = config
        self.cli_nid_aut = nid_aut
        self.cli_nid_ses = nid_ses

    def get_auth_cookies(self) -> tuple[str | None, str | None]:
        """Get authentication cookies with CLI override support.

        Returns:
            Tuple of (nid_aut, nid_ses) cookie values.
        """
        return self.config.get_auth_cookies(
            cli_nid_aut=self.cli_nid_aut,
            cli_nid_ses=self.cli_nid_ses,
        )
