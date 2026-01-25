"""Tests for chat output writers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from chzzk.cli.writers import (
    JsonlWriter,
    OutputFormat,
    TextWriter,
    create_writer,
)


@pytest.fixture
def mock_chat_message() -> MagicMock:
    """Create a mock ChatMessage."""
    msg = MagicMock()
    msg.user_id_hash = "user123"
    msg.nickname = "TestUser"
    msg.content = "Hello, world!"
    msg.profile = MagicMock()
    msg.profile.badge = {"name": "VIP"}
    return msg


@pytest.fixture
def mock_chat_message_no_badge() -> MagicMock:
    """Create a mock ChatMessage without badge."""
    msg = MagicMock()
    msg.user_id_hash = "user456"
    msg.nickname = "NoBadgeUser"
    msg.content = "No badge here"
    msg.profile = None
    return msg


@pytest.fixture
def mock_donation_message() -> MagicMock:
    """Create a mock DonationMessage."""
    msg = MagicMock()
    msg.user_id_hash = "donor789"
    msg.nickname = "GenerousDonor"
    msg.content = "Great stream!"
    msg.pay_amount = 10000
    return msg


@pytest.fixture
def mock_donation_message_no_content() -> MagicMock:
    """Create a mock DonationMessage without content."""
    msg = MagicMock()
    msg.user_id_hash = "donor999"
    msg.nickname = "SilentDonor"
    msg.content = None
    msg.pay_amount = 5000
    return msg


class TestJsonlWriter:
    """Tests for JsonlWriter."""

    def test_write_chat(self, tmp_path: Path, mock_chat_message: MagicMock) -> None:
        """Test writing a chat message in JSONL format."""
        output_file = tmp_path / "chat.jsonl"
        writer = JsonlWriter(output_file)

        writer.write_chat(mock_chat_message)
        writer.close()

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["type"] == "chat"
        assert data["user_id_hash"] == "user123"
        assert data["nickname"] == "TestUser"
        assert data["content"] == "Hello, world!"
        assert data["badge"] == "VIP"
        assert "timestamp" in data

    def test_write_chat_no_badge(
        self, tmp_path: Path, mock_chat_message_no_badge: MagicMock
    ) -> None:
        """Test writing a chat message without badge."""
        output_file = tmp_path / "chat.jsonl"
        writer = JsonlWriter(output_file)

        writer.write_chat(mock_chat_message_no_badge)
        writer.close()

        lines = output_file.read_text().strip().split("\n")
        data = json.loads(lines[0])
        assert data["badge"] is None

    def test_write_donation(self, tmp_path: Path, mock_donation_message: MagicMock) -> None:
        """Test writing a donation message in JSONL format."""
        output_file = tmp_path / "chat.jsonl"
        writer = JsonlWriter(output_file)

        writer.write_donation(mock_donation_message)
        writer.close()

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["type"] == "donation"
        assert data["user_id_hash"] == "donor789"
        assert data["nickname"] == "GenerousDonor"
        assert data["content"] == "Great stream!"
        assert data["pay_amount"] == 10000
        assert "timestamp" in data

    def test_write_sent(self, tmp_path: Path) -> None:
        """Test writing a sent message in JSONL format."""
        output_file = tmp_path / "chat.jsonl"
        writer = JsonlWriter(output_file)

        writer.write_sent("My sent message")
        writer.close()

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["type"] == "sent"
        assert data["content"] == "My sent message"
        assert "timestamp" in data

    def test_multiple_writes(
        self, tmp_path: Path, mock_chat_message: MagicMock, mock_donation_message: MagicMock
    ) -> None:
        """Test writing multiple messages."""
        output_file = tmp_path / "chat.jsonl"
        writer = JsonlWriter(output_file)

        writer.write_chat(mock_chat_message)
        writer.write_donation(mock_donation_message)
        writer.write_sent("Hello!")
        writer.close()

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 3

        assert json.loads(lines[0])["type"] == "chat"
        assert json.loads(lines[1])["type"] == "donation"
        assert json.loads(lines[2])["type"] == "sent"

    def test_context_manager(self, tmp_path: Path, mock_chat_message: MagicMock) -> None:
        """Test using writer as context manager."""
        output_file = tmp_path / "chat.jsonl"

        with JsonlWriter(output_file) as writer:
            writer.write_chat(mock_chat_message)

        # File should be readable after context manager exits
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 1

    def test_append_mode(self, tmp_path: Path, mock_chat_message: MagicMock) -> None:
        """Test that writer appends to existing file."""
        output_file = tmp_path / "chat.jsonl"
        output_file.write_text('{"existing": true}\n')

        writer = JsonlWriter(output_file)
        writer.write_chat(mock_chat_message)
        writer.close()

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["existing"] is True
        assert json.loads(lines[1])["type"] == "chat"

    def test_unicode_content(self, tmp_path: Path) -> None:
        """Test writing unicode content."""
        output_file = tmp_path / "chat.jsonl"
        writer = JsonlWriter(output_file)

        msg = MagicMock()
        msg.user_id_hash = "user123"
        msg.nickname = "한글유저"
        msg.content = "안녕하세요! 🎉"
        msg.profile = None

        writer.write_chat(msg)
        writer.close()

        lines = output_file.read_text(encoding="utf-8").strip().split("\n")
        data = json.loads(lines[0])
        assert data["nickname"] == "한글유저"
        assert data["content"] == "안녕하세요! 🎉"


class TestTextWriter:
    """Tests for TextWriter."""

    def test_write_chat(self, tmp_path: Path, mock_chat_message: MagicMock) -> None:
        """Test writing a chat message in text format."""
        output_file = tmp_path / "chat.txt"
        writer = TextWriter(output_file)

        writer.write_chat(mock_chat_message)
        writer.close()

        content = output_file.read_text()
        assert "[VIP] TestUser: Hello, world!" in content
        # Check timestamp format [HH:MM:SS]
        assert content.startswith("[")
        assert "]" in content

    def test_write_chat_no_badge(
        self, tmp_path: Path, mock_chat_message_no_badge: MagicMock
    ) -> None:
        """Test writing a chat message without badge."""
        output_file = tmp_path / "chat.txt"
        writer = TextWriter(output_file)

        writer.write_chat(mock_chat_message_no_badge)
        writer.close()

        content = output_file.read_text()
        assert "NoBadgeUser: No badge here" in content
        assert "[VIP]" not in content

    def test_write_donation(self, tmp_path: Path, mock_donation_message: MagicMock) -> None:
        """Test writing a donation message in text format."""
        output_file = tmp_path / "chat.txt"
        writer = TextWriter(output_file)

        writer.write_donation(mock_donation_message)
        writer.close()

        content = output_file.read_text()
        assert "10000원 GenerousDonor: Great stream!" in content

    def test_write_donation_no_content(
        self, tmp_path: Path, mock_donation_message_no_content: MagicMock
    ) -> None:
        """Test writing a donation message without content."""
        output_file = tmp_path / "chat.txt"
        writer = TextWriter(output_file)

        writer.write_donation(mock_donation_message_no_content)
        writer.close()

        content = output_file.read_text()
        assert "5000원 SilentDonor:" in content

    def test_write_sent(self, tmp_path: Path) -> None:
        """Test writing a sent message in text format."""
        output_file = tmp_path / "chat.txt"
        writer = TextWriter(output_file)

        writer.write_sent("My sent message")
        writer.close()

        content = output_file.read_text()
        assert "> My sent message" in content

    def test_context_manager(self, tmp_path: Path, mock_chat_message: MagicMock) -> None:
        """Test using writer as context manager."""
        output_file = tmp_path / "chat.txt"

        with TextWriter(output_file) as writer:
            writer.write_chat(mock_chat_message)

        content = output_file.read_text()
        assert "TestUser" in content


class TestCreateWriter:
    """Tests for create_writer factory function."""

    def test_create_jsonl_writer(self, tmp_path: Path) -> None:
        """Test creating a JSONL writer."""
        output_file = tmp_path / "chat.jsonl"
        writer = create_writer(output_file, OutputFormat.JSONL)

        assert isinstance(writer, JsonlWriter)
        writer.close()

    def test_create_txt_writer(self, tmp_path: Path) -> None:
        """Test creating a text writer."""
        output_file = tmp_path / "chat.txt"
        writer = create_writer(output_file, OutputFormat.TXT)

        assert isinstance(writer, TextWriter)
        writer.close()

    def test_create_writer_with_string_format(self, tmp_path: Path) -> None:
        """Test creating writer with string format."""
        output_file = tmp_path / "chat.jsonl"
        writer = create_writer(output_file, "jsonl")

        assert isinstance(writer, JsonlWriter)
        writer.close()

    def test_create_writer_invalid_format(self, tmp_path: Path) -> None:
        """Test creating writer with invalid format."""
        output_file = tmp_path / "chat.xml"

        with pytest.raises(ValueError, match="is not a valid OutputFormat"):
            create_writer(output_file, "xml")  # type: ignore[arg-type]


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_jsonl_value(self) -> None:
        """Test JSONL format value."""
        assert OutputFormat.JSONL == "jsonl"

    def test_txt_value(self) -> None:
        """Test TXT format value."""
        assert OutputFormat.TXT == "txt"

    def test_from_string(self) -> None:
        """Test creating OutputFormat from string."""
        assert OutputFormat("jsonl") == OutputFormat.JSONL
        assert OutputFormat("txt") == OutputFormat.TXT
