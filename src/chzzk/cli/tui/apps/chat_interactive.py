"""Interactive chat TUI application for Chzzk CLI."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Static

from chzzk.cli.tui.base import ChzzkApp
from chzzk.cli.tui.widgets.chat import ChatInput, ChatMessageList
from chzzk.constants import StatusText
from chzzk.exceptions import ChatConnectionError, ChatNotLiveError
from chzzk.unofficial import AsyncUnofficialChzzkClient, ChatMessage, DonationMessage

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager
    from chzzk.cli.writers import ChatWriter
    from chzzk.unofficial.chat.client import AsyncUnofficialChatClient

logger = logging.getLogger("chzzk.cli.tui.chat_interactive")


class InteractiveChatApp(ChzzkApp):
    """TUI application for interactive chat with message sending.

    Combines chat viewing with an input field for sending messages.
    Requires authentication to send messages.
    """

    TITLE = "Chzzk Interactive Chat"

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    DEFAULT_CSS = """
    InteractiveChatApp {
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
        padding: 0 1;
    }

    #chat-messages {
        height: 1fr;
    }

    #chat-input {
        dock: bottom;
        height: 3;
        margin: 0 1 1 1;
    }

    /* Inline mode styles - compact layout */
    InteractiveChatApp.-inline-mode #header {
        display: none;
    }

    InteractiveChatApp.-inline-mode Footer {
        display: none;
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
        inline_mode: bool = False,
        writer: ChatWriter | None = None,
    ) -> None:
        """Initialize the interactive chat app.

        Args:
            config: Configuration manager.
            channel_id: Channel ID to chat in.
            nid_aut: NID_AUT cookie value (required for sending).
            nid_ses: NID_SES cookie value (required for sending).
            allow_offline: Allow connecting when channel is offline.
            inline_mode: Run in inline mode with compact layout.
            writer: Optional chat writer for logging messages to file.
        """
        super().__init__(config=config, nid_aut=nid_aut, nid_ses=nid_ses)
        self.channel_id = channel_id
        self.allow_offline = allow_offline
        self._inline_mode = inline_mode
        self._channel_name: str | None = None
        self._client: AsyncUnofficialChzzkClient | None = None
        self._chat: AsyncUnofficialChatClient | None = None
        self._chat_task: asyncio.Task | None = None
        self._error_message: str | None = None
        self._connected = False
        self._writer = writer

    def compose(self) -> ComposeResult:
        """Compose the interactive chat UI."""
        yield Static("Chzzk Interactive Chat", id="header")
        yield Static("Connecting...", id="status", classes="status-connecting")
        with VerticalScroll(id="chat-container"):
            yield ChatMessageList(id="chat-messages")
        yield ChatInput(placeholder="Type a message and press Enter...", id="chat-input")
        yield Footer()

    async def on_mount(self) -> None:
        """Start chat connection when mounted."""
        # Apply inline mode class if needed
        if self._inline_mode:
            self.add_class("-inline-mode")

        # Verify authentication
        nid_aut, nid_ses = self.get_auth_cookies()
        if not nid_aut or not nid_ses:
            status_widget = self.query_one("#status", Static)
            status_widget.update("Authentication required to send messages")
            status_widget.set_class(True, "status-disconnected")
            self._error_message = "Authentication required"
            # Disable input
            chat_input = self.query_one("#chat-input", ChatInput)
            chat_input.disabled = True
            return

        self._chat_task = asyncio.create_task(self._run_chat())

        # Focus the input
        chat_input = self.query_one("#chat-input", ChatInput)
        chat_input.focus()

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
        chat_input = self.query_one("#chat-input", ChatInput)

        try:
            async with AsyncUnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
                self._client = client
                chat = client.create_chat_client()
                self._chat = chat

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
                    chat_input.disabled = True
                    return

                # Connect to chat
                try:
                    status_widget.update(f"Connecting to {self._channel_name}...")
                    await chat.connect(self.channel_id, allow_offline=self.allow_offline)

                    self._connected = True
                    status_widget.update(f"Connected - {self._channel_name} ({status_text})")
                    status_widget.set_class(False, "status-connecting")
                    status_widget.set_class(True, "status-connected")
                    chat_list.add_system_message(
                        f"Connected to {self._channel_name}. You can now send messages.",
                        style="green",
                    )

                except ChatNotLiveError:
                    self._error_message = "Channel is not live"
                    status_widget.update(
                        f"{self._channel_name} is not live (use --offline to connect anyway)"
                    )
                    status_widget.set_class(False, "status-connecting")
                    status_widget.set_class(True, "status-disconnected")
                    chat_input.disabled = True
                    return

                except ChatConnectionError as e:
                    logger.error(f"Failed to connect to chat: {e}")
                    self._error_message = str(e)
                    status_widget.update(f"Connection error: {e}")
                    status_widget.set_class(False, "status-connecting")
                    status_widget.set_class(True, "status-disconnected")
                    chat_input.disabled = True
                    return

                # Run chat client
                try:
                    await chat.run_forever()
                except asyncio.CancelledError:
                    pass
                finally:
                    self._connected = False
                    status_widget.update("Disconnected")
                    status_widget.set_class(False, "status-connected")
                    status_widget.set_class(True, "status-disconnected")
                    chat_input.disabled = True

        except Exception as e:
            logger.exception(f"Chat error: {e}")
            self._error_message = str(e)
            status_widget.update(f"Error: {e}")
            status_widget.set_class(True, "status-disconnected")
            chat_input.disabled = True

    @on(ChatInput.MessageSubmitted)
    async def on_message_submitted(self, event: ChatInput.MessageSubmitted) -> None:
        """Handle message submission from chat input.

        Args:
            event: The message submitted event.
        """
        if not self._connected or not self._chat:
            chat_list = self.query_one("#chat-messages", ChatMessageList)
            chat_list.add_system_message("Not connected", style="red")
            return

        content = event.content
        chat_list = self.query_one("#chat-messages", ChatMessageList)

        try:
            await self._chat.send_message(content)
            chat_list.add_sent_message(content)
            if self._writer:
                self._writer.write_sent(content)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            chat_list.add_system_message(f"Failed to send: {e}", style="red")

    def action_page_up(self) -> None:
        """Scroll chat messages up."""
        chat_list = self.query_one("#chat-messages", ChatMessageList)
        chat_list.scroll_page_up()

    def action_page_down(self) -> None:
        """Scroll chat messages down."""
        chat_list = self.query_one("#chat-messages", ChatMessageList)
        chat_list.scroll_page_down()

    @property
    def error_message(self) -> str | None:
        """Get any error that occurred during chat."""
        return self._error_message
