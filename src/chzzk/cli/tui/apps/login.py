"""Login TUI application for Chzzk CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Button, Footer, Label, Static

from chzzk.cli.tui.base import ChzzkApp
from chzzk.cli.tui.widgets.input import MaskedInput

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager


@dataclass
class LoginResult:
    """Result of login operation."""

    success: bool
    nid_aut: str | None = None
    nid_ses: str | None = None
    cancelled: bool = False


class LoginApp(ChzzkApp):
    """TUI application for entering Naver authentication cookies.

    Provides masked input fields for NID_AUT and NID_SES cookies
    with validation and save functionality.
    """

    TITLE = "Chzzk Login"

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    DEFAULT_CSS = """
    LoginApp {
        align: center middle;
    }

    #login-container {
        width: 60;
        height: auto;
        border: round $primary;
        padding: 1 2;
    }

    #login-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #login-description {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    .field-container {
        height: auto;
        margin: 1 0;
    }

    .field-label {
        margin-bottom: 0;
    }

    #save-button {
        width: 100%;
        margin-top: 1;
    }

    #status-message {
        text-align: center;
        margin-top: 1;
        height: 1;
    }

    .success {
        color: $success;
    }

    .error {
        color: $error;
    }
    """

    def __init__(
        self,
        config: ConfigManager,
        nid_aut: str | None = None,
        nid_ses: str | None = None,
    ) -> None:
        """Initialize the login app.

        Args:
            config: Configuration manager for saving cookies.
            nid_aut: Pre-filled NID_AUT value (optional).
            nid_ses: Pre-filled NID_SES value (optional).
        """
        super().__init__(config=config, nid_aut=nid_aut, nid_ses=nid_ses)
        self._result = LoginResult(success=False)
        self._prefill_nid_aut = nid_aut
        self._prefill_nid_ses = nid_ses

    def compose(self) -> ComposeResult:
        """Compose the login UI."""
        with Container(id="login-container"):
            yield Static("Chzzk Login", id="login-title")
            yield Static(
                "Enter your Naver authentication cookies",
                id="login-description",
            )

            with Vertical(classes="field-container"):
                yield Label("NID_AUT Cookie:", classes="field-label")
                yield MaskedInput(
                    placeholder="Enter NID_AUT cookie value",
                    id="nid-aut-input",
                )

            with Vertical(classes="field-container"):
                yield Label("NID_SES Cookie:", classes="field-label")
                yield MaskedInput(
                    placeholder="Enter NID_SES cookie value",
                    id="nid-ses-input",
                )

            yield Button("Save Cookies", variant="primary", id="save-button")
            yield Static("", id="status-message")

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event to pre-fill values if provided."""
        if self._prefill_nid_aut:
            nid_aut_input = self.query_one("#nid-aut-input", MaskedInput)
            nid_aut_input.value = self._prefill_nid_aut

        if self._prefill_nid_ses:
            nid_ses_input = self.query_one("#nid-ses-input", MaskedInput)
            nid_ses_input.value = self._prefill_nid_ses

        # Focus the first empty field
        nid_aut_input = self.query_one("#nid-aut-input", MaskedInput)
        if not nid_aut_input.value:
            nid_aut_input.focus()
        else:
            nid_ses_input = self.query_one("#nid-ses-input", MaskedInput)
            if not nid_ses_input.value:
                nid_ses_input.focus()

    @on(Button.Pressed, "#save-button")
    def on_save_button(self) -> None:
        """Handle save button press."""
        self.action_save()

    def action_save(self) -> None:
        """Save the cookie values."""
        nid_aut_input = self.query_one("#nid-aut-input", MaskedInput)
        nid_ses_input = self.query_one("#nid-ses-input", MaskedInput)
        status = self.query_one("#status-message", Static)

        nid_aut = nid_aut_input.value.strip()
        nid_ses = nid_ses_input.value.strip()

        # Validate inputs
        if not nid_aut_input.is_valid:
            status.update("Invalid NID_AUT cookie value")
            status.set_class(True, "error")
            status.set_class(False, "success")
            nid_aut_input.focus()
            return

        if not nid_ses_input.is_valid:
            status.update("Invalid NID_SES cookie value")
            status.set_class(True, "error")
            status.set_class(False, "success")
            nid_ses_input.focus()
            return

        # Save cookies
        try:
            self.config.save_cookies(nid_aut, nid_ses)
            self._result = LoginResult(
                success=True,
                nid_aut=nid_aut,
                nid_ses=nid_ses,
            )
            status.update("Cookies saved successfully!")
            status.set_class(False, "error")
            status.set_class(True, "success")
            # Exit after brief delay to show success message
            self.set_timer(0.5, self.exit)
        except Exception as e:
            status.update(f"Failed to save: {e}")
            status.set_class(True, "error")
            status.set_class(False, "success")

    def action_cancel(self) -> None:
        """Cancel login and exit."""
        self._result = LoginResult(success=False, cancelled=True)
        self.exit()

    @property
    def result(self) -> LoginResult:
        """Get the login result."""
        return self._result
