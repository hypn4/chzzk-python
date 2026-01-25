"""Chat viewer TUI application for Chzzk CLI."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Static

from chzzk.cli.formatter import ChatFormatter, FormatConfig
from chzzk.cli.tui.base import ChzzkApp
from chzzk.cli.tui.widgets.chat import ChatMessageList
from chzzk.constants import StatusText
from chzzk.exceptions import ChatConnectionError, ChatNotLiveError
from chzzk.unofficial import AsyncUnofficialChzzkClient, ChatMessage, DonationMessage

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager
    from chzzk.cli.writers import ChatWriter

logger = logging.getLogger("chzzk.cli.tui.chat_viewer")


class ChatViewerApp(ChzzkApp):
    """TUI application for viewing real-time chat messages.

    Displays chat and donation messages in a scrollable view
    with keyboard controls for navigation.
    """

    TITLE = "Chzzk Chat Viewer"

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("q", "quit", "Quit"),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("home", "scroll_home", "Top", show=False),
        Binding("end", "scroll_end", "Bottom", show=False),
    ]

    DEFAULT_CSS = """
    ChatViewerApp {
        layout: vertical;
    }

    #header {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }

    #status {
        dock: top;
        height: 1;
        background: $surface;
        padding: 0 1;
    }

    .status-connected {
        color: $success;
    }

    .status-connecting {
        color: $warning;
    }

    .status-disconnected {
        color: $error;
    }

    #chat-container {
        height: 1fr;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        config: ConfigManager,
        channel_id: str,
        *,
        nid_aut: str | None = None,
        nid_ses: str | None = None,
        allow_offline: bool = False,
        writer: ChatWriter | None = None,
        format_config: FormatConfig | None = None,
    ) -> None:
        """Initialize the chat viewer app.

        Args:
            config: Configuration manager.
            channel_id: Channel ID to watch.
            nid_aut: NID_AUT cookie value (optional).
            nid_ses: NID_SES cookie value (optional).
            allow_offline: Allow connecting when channel is offline.
            writer: Optional chat writer for logging messages to file.
            format_config: Format configuration for chat messages.
        """
        super().__init__(config=config, nid_aut=nid_aut, nid_ses=nid_ses)
        self.channel_id = channel_id
        self.allow_offline = allow_offline
        self._channel_name: str | None = None
        self._client: AsyncUnofficialChzzkClient | None = None
        self._chat_task: asyncio.Task | None = None
        self._error_message: str | None = None
        self._writer = writer
        self._formatter = ChatFormatter(format_config)

    def compose(self) -> ComposeResult:
        """Compose the chat viewer UI."""
        yield Static("Chzzk Chat Viewer", id="header")
        yield Static("Connecting...", id="status", classes="status-connecting")
        with Container(id="chat-container"):
            yield ChatMessageList(formatter=self._formatter, id="chat-messages")
        yield Footer()

    async def on_mount(self) -> None:
        """Start chat connection when mounted."""
        self._chat_task = asyncio.create_task(self._run_chat())

    async def on_unmount(self) -> None:
        """Clean up chat connection when unmounted."""
        if self._chat_task:
            self._chat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._chat_task

    async def _run_chat(self) -> None:
        """Run the chat connection and message handling."""
        nid_aut, nid_ses = self.get_auth_cookies()
        status_widget = self.query_one("#status", Static)
        chat_list = self.query_one("#chat-messages", ChatMessageList)

        try:
            async with AsyncUnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
                self._client = client
                chat = client.create_chat_client()

                # Register message handlers
                @chat.on_chat
                async def handle_chat(msg: ChatMessage) -> None:
                    chat_list.add_chat_message(msg)
                    if self._writer:
                        self._writer.write_chat(msg)

                @chat.on_donation
                async def handle_donation(msg: DonationMessage) -> None:
                    chat_list.add_donation_message(msg)
                    if self._writer:
                        self._writer.write_donation(msg)

                # Get live detail
                try:
                    live_detail = await client.live.get_live_detail(self.channel_id)
                    self._channel_name = live_detail.channel_name or self.channel_id
                    status_text = StatusText.LIVE if live_detail.is_live else StatusText.OFFLINE
                    self.title = f"Chzzk - {self._channel_name}"
                except Exception as e:
                    logger.error(f"Failed to get live detail: {e}")
                    self._error_message = str(e)
                    status_widget.update(f"Error: {e}")
                    status_widget.set_class(True, "status-disconnected")
                    return

                # Connect to chat
                try:
                    status_widget.update(f"Connecting to {self._channel_name}...")
                    await chat.connect(self.channel_id, allow_offline=self.allow_offline)

                    status_widget.update(f"Connected - {self._channel_name} ({status_text})")
                    status_widget.set_class(False, "status-connecting")
                    status_widget.set_class(True, "status-connected")
                    chat_list.add_system_message(
                        f"Connected to {self._channel_name}", style="green"
                    )

                except ChatNotLiveError:
                    self._error_message = "Channel is not live"
                    status_widget.update(
                        f"{self._channel_name} is not live (use --offline to connect anyway)"
                    )
                    status_widget.set_class(False, "status-connecting")
                    status_widget.set_class(True, "status-disconnected")
                    return

                except ChatConnectionError as e:
                    logger.error(f"Failed to connect to chat: {e}")
                    self._error_message = str(e)
                    status_widget.update(f"Connection error: {e}")
                    status_widget.set_class(False, "status-connecting")
                    status_widget.set_class(True, "status-disconnected")
                    return

                # Run chat client
                try:
                    await chat.run_forever()
                except asyncio.CancelledError:
                    pass
                finally:
                    status_widget.update("Disconnected")
                    status_widget.set_class(False, "status-connected")
                    status_widget.set_class(True, "status-disconnected")

        except Exception as e:
            logger.exception(f"Chat error: {e}")
            self._error_message = str(e)
            status_widget.update(f"Error: {e}")
            status_widget.set_class(True, "status-disconnected")

    def action_page_up(self) -> None:
        """Scroll chat messages up."""
        chat_list = self.query_one("#chat-messages", ChatMessageList)
        chat_list.scroll_page_up()

    def action_page_down(self) -> None:
        """Scroll chat messages down."""
        chat_list = self.query_one("#chat-messages", ChatMessageList)
        chat_list.scroll_page_down()

    def action_scroll_home(self) -> None:
        """Scroll to the beginning of chat."""
        chat_list = self.query_one("#chat-messages", ChatMessageList)
        chat_list.scroll_home()

    def action_scroll_end(self) -> None:
        """Scroll to the end of chat."""
        chat_list = self.query_one("#chat-messages", ChatMessageList)
        chat_list.scroll_end()

    @property
    def error_message(self) -> str | None:
        """Get any error that occurred during chat."""
        return self._error_message
