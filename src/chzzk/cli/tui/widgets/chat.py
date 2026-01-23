"""Chat widgets for Chzzk TUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from rich.text import Text
from textual import on
from textual.message import Message
from textual.widgets import Input, RichLog

if TYPE_CHECKING:
    from chzzk.unofficial import ChatMessage, DonationMessage


@dataclass
class FormattedMessage:
    """A formatted chat message for display."""

    timestamp: datetime
    nickname: str
    content: str
    is_donation: bool = False
    pay_amount: int | None = None
    badge_name: str | None = None
    is_self: bool = False


class ChatMessageList(RichLog):
    """Scrollable list of chat messages.

    Displays chat and donation messages with formatting.
    Supports scrolling with PageUp/PageDown and auto-scroll on new messages.
    """

    DEFAULT_CSS = """
    ChatMessageList {
        border: round $primary;
        height: 1fr;
        scrollbar-gutter: stable;
    }
    """

    MAX_MESSAGES = 1000

    def __init__(
        self,
        *,
        max_messages: int = MAX_MESSAGES,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the chat message list.

        Args:
            max_messages: Maximum number of messages to keep in buffer.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(
            highlight=True,
            markup=True,
            wrap=True,
            auto_scroll=True,
            id=id,
            classes=classes,
        )
        self.max_messages = max_messages
        self._message_count = 0

    def add_chat_message(self, msg: ChatMessage) -> None:
        """Add a chat message to the list.

        Args:
            msg: The chat message to display.
        """
        formatted = self._format_chat_message(msg)
        self._write_message(formatted)

    def add_donation_message(self, msg: DonationMessage) -> None:
        """Add a donation message to the list.

        Args:
            msg: The donation message to display.
        """
        formatted = self._format_donation_message(msg)
        self._write_message(formatted)

    def add_sent_message(self, content: str) -> None:
        """Add a message sent by the user.

        Args:
            content: The message content that was sent.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(f"{timestamp} ", style="dim")
        text.append("> ", style="green bold")
        text.append(content, style="green")
        self._write_message(text)

    def add_system_message(self, content: str, style: str = "yellow") -> None:
        """Add a system notification message.

        Args:
            content: The system message content.
            style: Rich style for the message.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(f"{timestamp} ", style="dim")
        text.append(content, style=style)
        self._write_message(text)

    def _format_chat_message(self, msg: ChatMessage) -> Text:
        """Format a chat message for display.

        Args:
            msg: The chat message to format.

        Returns:
            Formatted Rich Text object.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(f"{timestamp} ", style="dim")

        # Add badge if present
        if msg.profile and msg.profile.badge:
            badge_name = msg.profile.badge.get("name")
            if badge_name:
                text.append(f"[{badge_name}] ", style="magenta")

        text.append(f"{msg.nickname}", style="cyan")
        text.append(": ")
        text.append(msg.content or "")

        return text

    def _format_donation_message(self, msg: DonationMessage) -> Text:
        """Format a donation message for display.

        Args:
            msg: The donation message to format.

        Returns:
            Formatted Rich Text object.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(f"{timestamp} ", style="dim")
        text.append(f"${msg.pay_amount} ", style="yellow bold")
        text.append(f"{msg.nickname}", style="magenta bold")
        text.append(": ")
        text.append(msg.content or "", style="white")

        return text

    def _write_message(self, text: Text) -> None:
        """Write a message to the log with buffer management.

        Args:
            text: The formatted text to write.
        """
        self.write(text)
        self._message_count += 1

        # Trim old messages if buffer exceeds limit
        if self._message_count > self.max_messages:
            self.clear()
            self._message_count = 0


class ChatInput(Input):
    """Input widget for composing chat messages.

    Sends a MessageSubmitted message when Enter is pressed.
    """

    DEFAULT_CSS = """
    ChatInput {
        dock: bottom;
        border: tall $primary;
        height: 3;
    }
    ChatInput:focus {
        border: tall $accent;
    }
    """

    @dataclass
    class MessageSubmitted(Message):
        """Posted when a message is submitted."""

        content: str
        """The message content."""

        input: ChatInput
        """The input widget that submitted the message."""

        @property
        def control(self) -> ChatInput:
            """Alias for Textual message protocol."""
            return self.input

    def __init__(
        self,
        placeholder: str = "Type a message...",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the chat input widget.

        Args:
            placeholder: Placeholder text when empty.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(placeholder=placeholder, id=id, classes=classes)

    @on(Input.Submitted)
    def on_submit(self, event: Input.Submitted) -> None:
        """Handle Enter key press to submit message.

        Args:
            event: The submit event.
        """
        content = self.value.strip()
        if content:
            self.post_message(self.MessageSubmitted(content=content, input=self))
            self.value = ""
