"""Chat output writers for CLI."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chzzk.unofficial import ChatMessage, DonationMessage


class OutputFormat(StrEnum):
    """Output format for chat messages."""

    JSONL = "jsonl"
    TXT = "txt"


class ChatWriter(ABC):
    """Abstract base class for chat message writers."""

    @abstractmethod
    def write_chat(self, msg: ChatMessage) -> None:
        """Write a chat message.

        Args:
            msg: The chat message to write.
        """
        ...

    @abstractmethod
    def write_donation(self, msg: DonationMessage) -> None:
        """Write a donation message.

        Args:
            msg: The donation message to write.
        """
        ...

    @abstractmethod
    def write_sent(self, content: str) -> None:
        """Write a sent message.

        Args:
            content: The message content that was sent.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the writer and release resources."""
        ...

    def __enter__(self) -> ChatWriter:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        """Context manager exit."""
        self.close()


class JsonlWriter(ChatWriter):
    """Writer that outputs chat messages in JSONL format."""

    def __init__(self, path: Path) -> None:
        """Initialize the JSONL writer.

        Args:
            path: Path to the output file.
        """
        self._path = path
        self._file = path.open("a", encoding="utf-8")

    def write_chat(self, msg: ChatMessage) -> None:
        """Write a chat message in JSONL format."""
        badge_name = None
        if msg.profile:
            # 1. Check profile.badge dict
            if msg.profile.badge:
                badge_name = msg.profile.badge.get("name") or msg.profile.badge.get("title")

            # 2. Check activity_badges list
            if not badge_name and msg.profile.activity_badges:
                for activity_badge in msg.profile.activity_badges:
                    if isinstance(activity_badge, dict):
                        badge_name = (
                            activity_badge.get("name")
                            or activity_badge.get("title")
                            or activity_badge.get("badgeName")
                        )
                        if badge_name:
                            break

        data = {
            "type": "chat",
            "timestamp": datetime.now().isoformat(),
            "user_id_hash": msg.user_id_hash,
            "nickname": msg.nickname,
            "content": msg.content,
            "badge": badge_name,
        }
        self._file.write(json.dumps(data, ensure_ascii=False) + "\n")
        self._file.flush()

    def write_donation(self, msg: DonationMessage) -> None:
        """Write a donation message in JSONL format."""
        data = {
            "type": "donation",
            "timestamp": datetime.now().isoformat(),
            "user_id_hash": msg.user_id_hash,
            "nickname": msg.nickname,
            "content": msg.content,
            "pay_amount": msg.pay_amount,
        }
        self._file.write(json.dumps(data, ensure_ascii=False) + "\n")
        self._file.flush()

    def write_sent(self, content: str) -> None:
        """Write a sent message in JSONL format."""
        data = {
            "type": "sent",
            "timestamp": datetime.now().isoformat(),
            "content": content,
        }
        self._file.write(json.dumps(data, ensure_ascii=False) + "\n")
        self._file.flush()

    def close(self) -> None:
        """Close the file."""
        if self._file and not self._file.closed:
            self._file.close()


class TextWriter(ChatWriter):
    """Writer that outputs chat messages in human-readable text format."""

    def __init__(self, path: Path) -> None:
        """Initialize the text writer.

        Args:
            path: Path to the output file.
        """
        self._path = path
        self._file = path.open("a", encoding="utf-8")

    def write_chat(self, msg: ChatMessage) -> None:
        """Write a chat message in text format."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        badge_name = None
        if msg.profile:
            # 1. Check profile.badge dict
            if msg.profile.badge:
                badge_name = msg.profile.badge.get("name") or msg.profile.badge.get("title")

            # 2. Check activity_badges list
            if not badge_name and msg.profile.activity_badges:
                for activity_badge in msg.profile.activity_badges:
                    if isinstance(activity_badge, dict):
                        badge_name = (
                            activity_badge.get("name")
                            or activity_badge.get("title")
                            or activity_badge.get("badgeName")
                        )
                        if badge_name:
                            break

        badge = f"[{badge_name}] " if badge_name else ""
        self._file.write(f"[{timestamp}] {badge}{msg.nickname}: {msg.content}\n")
        self._file.flush()

    def write_donation(self, msg: DonationMessage) -> None:
        """Write a donation message in text format."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        content = msg.content or ""
        self._file.write(f"[{timestamp}] {msg.pay_amount}원 {msg.nickname}: {content}\n")
        self._file.flush()

    def write_sent(self, content: str) -> None:
        """Write a sent message in text format."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._file.write(f"[{timestamp}] > {content}\n")
        self._file.flush()

    def close(self) -> None:
        """Close the file."""
        if self._file and not self._file.closed:
            self._file.close()


def create_writer(path: Path, format: OutputFormat | str) -> ChatWriter:
    """Create a chat writer for the specified format.

    Args:
        path: Path to the output file.
        format: Output format (jsonl or txt).

    Returns:
        A ChatWriter instance.

    Raises:
        ValueError: If the format is not supported.
    """
    format_enum = OutputFormat(format) if isinstance(format, str) else format

    if format_enum == OutputFormat.JSONL:
        return JsonlWriter(path)
    elif format_enum == OutputFormat.TXT:
        return TextWriter(path)
    else:
        raise ValueError(f"Unsupported output format: {format}")
