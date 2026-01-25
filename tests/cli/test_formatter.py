"""Tests for chat message formatter."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from chzzk.cli.formatter import ChatFormatter, FormatConfig


class TestFormatConfig:
    """Tests for FormatConfig."""

    def test_default_values(self) -> None:
        """Test default format values."""
        config = FormatConfig()

        assert "{time}" in config.chat_format
        assert "{name}" in config.chat_format
        assert "{msg}" in config.chat_format
        assert "{badge}" in config.chat_format

        assert "{amount}" in config.donation_format
        assert "{badge}" in config.donation_format
        assert "{time}" in config.sent_format
        assert "{style}" in config.system_format
        assert config.time_format == "%H:%M:%S"

    def test_from_env_and_cli_defaults(self) -> None:
        """Test from_env_and_cli with no arguments uses defaults."""
        config = FormatConfig.from_env_and_cli()
        defaults = FormatConfig()

        assert config.chat_format == defaults.chat_format
        assert config.donation_format == defaults.donation_format
        assert config.sent_format == defaults.sent_format
        assert config.time_format == defaults.time_format

    def test_from_env_and_cli_env_override(self) -> None:
        """Test environment variables override defaults."""
        config = FormatConfig.from_env_and_cli(
            env_chat_format="{name}: {msg}",
            env_time_format="%H:%M",
        )

        assert config.chat_format == "{name}: {msg}"
        assert config.time_format == "%H:%M"
        # Defaults should be preserved for unset values
        assert config.donation_format == FormatConfig().donation_format

    def test_from_env_and_cli_cli_override(self) -> None:
        """Test CLI options override environment variables."""
        config = FormatConfig.from_env_and_cli(
            cli_chat_format="{name} says: {msg}",
            env_chat_format="{name}: {msg}",
        )

        assert config.chat_format == "{name} says: {msg}"

    def test_from_env_and_cli_priority(self) -> None:
        """Test priority: CLI > ENV > default."""
        config = FormatConfig.from_env_and_cli(
            cli_chat_format="cli format",
            env_chat_format="env format",
            env_donation_format="env donation",
        )

        assert config.chat_format == "cli format"
        assert config.donation_format == "env donation"
        assert config.sent_format == FormatConfig().sent_format


class TestChatFormatter:
    """Tests for ChatFormatter."""

    @pytest.fixture
    def mock_chat_message(self) -> MagicMock:
        """Create a mock chat message."""
        msg = MagicMock()
        msg.nickname = "TestUser"
        msg.content = "Hello, world!"
        msg.message_time = None
        msg.profile = MagicMock()
        msg.profile.badge = {"name": "VIP"}
        msg.profile.activity_badges = []
        msg.profile.verified_mark = False
        msg.profile.user_role_code = None
        return msg

    @pytest.fixture
    def mock_chat_message_no_badge(self) -> MagicMock:
        """Create a mock chat message without badge."""
        msg = MagicMock()
        msg.nickname = "TestUser"
        msg.content = "Hello!"
        msg.message_time = None
        msg.profile = None
        return msg

    @pytest.fixture
    def mock_chat_message_activity_badge(self) -> MagicMock:
        """Create a mock chat message with activity badge."""
        msg = MagicMock()
        msg.nickname = "TestUser"
        msg.content = "Hello from subscriber!"
        msg.message_time = None
        msg.profile = MagicMock()
        msg.profile.badge = None
        msg.profile.activity_badges = [{"name": "구독자", "imageUrl": "http://..."}]
        msg.profile.verified_mark = False
        msg.profile.user_role_code = None
        return msg

    @pytest.fixture
    def mock_chat_message_badge_title_key(self) -> MagicMock:
        """Create a mock chat message with badge using 'title' key."""
        msg = MagicMock()
        msg.nickname = "TestUser"
        msg.content = "Hello!"
        msg.message_time = None
        msg.profile = MagicMock()
        msg.profile.badge = {"title": "매니저"}
        msg.profile.activity_badges = []
        msg.profile.verified_mark = False
        msg.profile.user_role_code = None
        return msg

    @pytest.fixture
    def mock_donation_message(self) -> MagicMock:
        """Create a mock donation message."""
        msg = MagicMock()
        msg.nickname = "Donor"
        msg.content = "Great stream!"
        msg.pay_amount = 1000
        msg.pay_type = "CHEESE"
        msg.donation_type = "CHAT"
        msg.message_time = None
        msg.extras = None
        msg.profile = None
        return msg

    @pytest.fixture
    def mock_donation_message_with_badge(self) -> MagicMock:
        """Create a mock donation message with badge."""
        msg = MagicMock()
        msg.nickname = "VIPDonor"
        msg.content = "Love the content!"
        msg.pay_amount = 5000
        msg.pay_type = "CHEESE"
        msg.donation_type = "CHAT"
        msg.message_time = None
        msg.extras = None
        msg.profile = MagicMock()
        msg.profile.badge = {"name": "치즈 후원자"}
        msg.profile.activity_badges = []
        msg.profile.verified_mark = False
        msg.profile.user_role_code = None
        return msg

    @pytest.fixture
    def mock_donation_message_with_activity_badge(self) -> MagicMock:
        """Create a mock donation message with activity badge."""
        msg = MagicMock()
        msg.nickname = "Subscriber"
        msg.content = "Subscribed!"
        msg.pay_amount = 3000
        msg.pay_type = "CHEESE"
        msg.donation_type = "CHAT"
        msg.message_time = None
        msg.extras = None
        msg.profile = MagicMock()
        msg.profile.badge = None
        msg.profile.activity_badges = [{"name": "구독자", "imageUrl": "http://..."}]
        msg.profile.verified_mark = False
        msg.profile.user_role_code = None
        return msg

    def test_format_chat_default(self, mock_chat_message: MagicMock) -> None:
        """Test default chat format."""
        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message)

        assert "TestUser" in result
        assert "Hello, world!" in result
        assert "[VIP]" in result

    def test_format_chat_no_badge(self, mock_chat_message_no_badge: MagicMock) -> None:
        """Test chat format without badge."""
        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message_no_badge)

        assert "TestUser" in result
        assert "Hello!" in result
        assert "[" not in result.split("TestUser")[0].split("]")[-1]

    def test_format_chat_activity_badge(self, mock_chat_message_activity_badge: MagicMock) -> None:
        """Test chat format with activity badge."""
        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message_activity_badge)

        assert "TestUser" in result
        assert "Hello from subscriber!" in result
        assert "[구독자]" in result

    def test_format_chat_badge_title_key(
        self, mock_chat_message_badge_title_key: MagicMock
    ) -> None:
        """Test chat format with badge using 'title' key instead of 'name'."""
        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message_badge_title_key)

        assert "TestUser" in result
        assert "[매니저]" in result

    def test_format_chat_custom_template(self, mock_chat_message: MagicMock) -> None:
        """Test custom chat format template."""
        config = FormatConfig(chat_format="{name} -> {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message)

        assert "TestUser -> Hello, world!" in result

    def test_format_donation(self, mock_donation_message: MagicMock) -> None:
        """Test donation format."""
        formatter = ChatFormatter()
        result = formatter.format_donation(mock_donation_message)

        assert "Donor" in result
        assert "Great stream!" in result
        assert "1000원" in result

    def test_format_donation_custom_template(self, mock_donation_message: MagicMock) -> None:
        """Test custom donation format template."""
        config = FormatConfig(donation_format="${amount} from {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message)

        assert "$1000 from Donor: Great stream!" in result

    def test_format_donation_with_badge(self, mock_donation_message_with_badge: MagicMock) -> None:
        """Test donation format with badge."""
        formatter = ChatFormatter()
        result = formatter.format_donation(mock_donation_message_with_badge)

        assert "VIPDonor" in result
        assert "Love the content!" in result
        assert "5000원" in result
        assert "[치즈 후원자]" in result

    def test_format_donation_with_activity_badge(
        self, mock_donation_message_with_activity_badge: MagicMock
    ) -> None:
        """Test donation format with activity badge."""
        formatter = ChatFormatter()
        result = formatter.format_donation(mock_donation_message_with_activity_badge)

        assert "Subscriber" in result
        assert "3000원" in result
        assert "[구독자]" in result

    def test_format_donation_no_badge(self, mock_donation_message: MagicMock) -> None:
        """Test donation format without badge shows no badge placeholder."""
        from rich.text import Text

        formatter = ChatFormatter()
        result = formatter.format_donation(mock_donation_message)

        assert "Donor" in result
        assert "1000원" in result

        # Check plain text has no badge brackets (Rich markup [] are stripped)
        plain = Text.from_markup(result).plain
        assert "Donor" in plain
        assert "1000원" in plain
        # Between amount and name, there should be no badge text
        amount_idx = plain.find("원")
        name_idx = plain.find("Donor")
        between = plain[amount_idx + 1 : name_idx]
        # Should only be whitespace between amount and name when no badge
        assert between.strip() == ""

    def test_format_sent(self) -> None:
        """Test sent message format."""
        formatter = ChatFormatter()
        result = formatter.format_sent("My message")

        assert "My message" in result
        assert ">" in result or "green" in result.lower()

    def test_format_sent_custom_template(self) -> None:
        """Test custom sent message format template."""
        config = FormatConfig(sent_format=">> {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_sent("My message")

        assert ">> My message" in result

    def test_format_system(self) -> None:
        """Test system message format."""
        formatter = ChatFormatter()
        result = formatter.format_system("Connected!", "green")

        assert "Connected!" in result

    def test_escape_markup(self, mock_chat_message: MagicMock) -> None:
        """Test Rich markup escaping in user content."""
        mock_chat_message.nickname = "User[Test]"
        mock_chat_message.content = "Hello [bold]world[/bold]!"

        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message)

        # The brackets should be escaped so they don't act as Rich markup
        assert "User\\[Test\\]" in result or "User[Test]" in result
        assert "\\[bold\\]" in result or "[bold]" in result

    def test_custom_time_format(self, mock_chat_message: MagicMock) -> None:
        """Test custom time format."""
        config = FormatConfig(time_format="%H:%M")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message)

        # Time should be in HH:MM format (no seconds)
        # This is a basic check - the actual time will vary
        assert "TestUser" in result

    def test_format_chat_text(self, mock_chat_message: MagicMock) -> None:
        """Test format_chat_text returns Rich Text."""
        from rich.text import Text

        formatter = ChatFormatter()
        result = formatter.format_chat_text(mock_chat_message)

        assert isinstance(result, Text)
        assert "TestUser" in result.plain
        assert "Hello, world!" in result.plain

    def test_format_donation_text(self, mock_donation_message: MagicMock) -> None:
        """Test format_donation_text returns Rich Text."""
        from rich.text import Text

        formatter = ChatFormatter()
        result = formatter.format_donation_text(mock_donation_message)

        assert isinstance(result, Text)
        assert "Donor" in result.plain
        assert "1000" in result.plain

    def test_format_sent_text(self) -> None:
        """Test format_sent_text returns Rich Text."""
        from rich.text import Text

        formatter = ChatFormatter()
        result = formatter.format_sent_text("Test message")

        assert isinstance(result, Text)
        assert "Test message" in result.plain

    def test_format_system_text(self) -> None:
        """Test format_system_text returns Rich Text."""
        from rich.text import Text

        formatter = ChatFormatter()
        result = formatter.format_system_text("System message", "yellow")

        assert isinstance(result, Text)
        assert "System message" in result.plain

    def test_empty_content(self, mock_chat_message: MagicMock) -> None:
        """Test handling empty content."""
        mock_chat_message.content = None
        mock_chat_message.nickname = "User"

        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message)

        assert "User" in result
        # Should not raise an error

    def test_empty_nickname(self, mock_chat_message: MagicMock) -> None:
        """Test handling empty nickname."""
        mock_chat_message.nickname = None
        mock_chat_message.content = "Content"

        formatter = ChatFormatter()
        result = formatter.format_chat(mock_chat_message)

        assert "Content" in result
        # Should not raise an error

    @pytest.fixture
    def mock_chat_message_verified(self) -> MagicMock:
        """Create a mock verified user chat message."""
        msg = MagicMock()
        msg.nickname = "VerifiedUser"
        msg.content = "Hello!"
        msg.message_time = None
        msg.profile = MagicMock()
        msg.profile.verified_mark = True
        msg.profile.user_role_code = "streamer"
        msg.profile.badge = None
        msg.profile.activity_badges = []
        return msg

    def test_format_chat_verified(self, mock_chat_message_verified: MagicMock) -> None:
        """Test chat format with verified user."""
        config = FormatConfig(chat_format="{verified}{name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message_verified)
        assert "✓VerifiedUser: Hello!" in result

    def test_format_chat_role(self, mock_chat_message_verified: MagicMock) -> None:
        """Test chat format with user role."""
        config = FormatConfig(chat_format="[{role}] {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message_verified)
        assert "[스트리머] VerifiedUser: Hello!" in result

    def test_format_chat_role_manager(self, mock_chat_message_verified: MagicMock) -> None:
        """Test chat format with manager role."""
        mock_chat_message_verified.profile.user_role_code = "streaming_channel_manager"
        config = FormatConfig(chat_format="[{role}] {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message_verified)
        assert "[매니저] VerifiedUser: Hello!" in result

    def test_format_chat_role_common_user(self, mock_chat_message_verified: MagicMock) -> None:
        """Test chat format with common user (empty role)."""
        mock_chat_message_verified.profile.user_role_code = "common_user"
        config = FormatConfig(chat_format="[{role}]{name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message_verified)
        assert "[]VerifiedUser: Hello!" in result

    def test_format_chat_server_time(self, mock_chat_message: MagicMock) -> None:
        """Test chat format with server time."""
        mock_chat_message.message_time = 1706000000000  # Unix timestamp in ms
        mock_chat_message.profile.verified_mark = False
        mock_chat_message.profile.user_role_code = None
        config = FormatConfig(chat_format="{server_time} {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message)
        # Server time should be formatted
        assert "TestUser: Hello, world!" in result
        # Time format should be present (HH:MM:SS)
        assert ":" in result.split(" ")[0]

    def test_format_chat_no_server_time(self, mock_chat_message: MagicMock) -> None:
        """Test chat format without server time returns empty string."""
        mock_chat_message.message_time = None
        mock_chat_message.profile.verified_mark = False
        mock_chat_message.profile.user_role_code = None
        config = FormatConfig(chat_format="|{server_time}| {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_chat(mock_chat_message)
        assert "|| TestUser: Hello, world!" in result

    @pytest.fixture
    def mock_donation_message_full(self) -> MagicMock:
        """Create a mock donation message with all fields."""
        msg = MagicMock()
        msg.nickname = "Donor"
        msg.content = "Great!"
        msg.pay_amount = 1000
        msg.pay_type = "CHEESE"
        msg.donation_type = "CHAT"
        msg.message_time = None
        msg.extras = None
        msg.profile = MagicMock()
        msg.profile.verified_mark = False
        msg.profile.user_role_code = "common_user"
        msg.profile.badge = None
        msg.profile.activity_badges = []
        return msg

    def test_format_donation_pay_type_cheese(self, mock_donation_message_full: MagicMock) -> None:
        """Test donation format with cheese pay type."""
        config = FormatConfig(donation_format="{amount}원({pay_type}) {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "1000원(치즈) Donor: Great!" in result

    def test_format_donation_pay_type_currency(self, mock_donation_message_full: MagicMock) -> None:
        """Test donation format with currency pay type."""
        mock_donation_message_full.pay_type = "CURRENCY"
        config = FormatConfig(donation_format="{amount}원({pay_type}) {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "1000원(현금) Donor: Great!" in result

    def test_format_donation_type_chat(self, mock_donation_message_full: MagicMock) -> None:
        """Test donation format with chat donation type."""
        config = FormatConfig(donation_format="[{donation_type}] {amount}원 {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "[채팅] 1000원 Donor: Great!" in result

    def test_format_donation_type_video(self, mock_donation_message_full: MagicMock) -> None:
        """Test donation format with video donation type."""
        mock_donation_message_full.donation_type = "VIDEO"
        config = FormatConfig(donation_format="[{donation_type}] {amount}원 {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "[영상] 1000원 Donor: Great!" in result

    @pytest.fixture
    def mock_donation_message_continuous(self) -> MagicMock:
        """Create a mock donation message with continuous days."""
        msg = MagicMock()
        msg.nickname = "LoyalDonor"
        msg.content = "Day 7!"
        msg.pay_amount = 5000
        msg.pay_type = "CURRENCY"
        msg.donation_type = "CHAT"
        msg.message_time = 1706000000000
        msg.extras = {"continuousDonationDays": 7}
        msg.profile = MagicMock()
        msg.profile.verified_mark = True
        msg.profile.user_role_code = "common_user"
        msg.profile.badge = None
        msg.profile.activity_badges = []
        return msg

    def test_format_donation_continuous_days(
        self, mock_donation_message_continuous: MagicMock
    ) -> None:
        """Test donation format with continuous donation days."""
        config = FormatConfig(donation_format="{continuous_days} {amount}원 {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_continuous)
        assert "7일 5000원 LoyalDonor: Day 7!" in result

    def test_format_donation_continuous_days_zero(
        self, mock_donation_message_full: MagicMock
    ) -> None:
        """Test donation format with zero continuous donation days."""
        mock_donation_message_full.extras = {"continuousDonationDays": 0}
        config = FormatConfig(donation_format="|{continuous_days}| {amount}원 {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "|| 1000원 Donor: Great!" in result

    def test_format_donation_no_extras(self, mock_donation_message_full: MagicMock) -> None:
        """Test donation format with no extras."""
        mock_donation_message_full.extras = None
        config = FormatConfig(donation_format="|{continuous_days}| {amount}원 {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "|| 1000원 Donor: Great!" in result

    def test_format_donation_verified(self, mock_donation_message_continuous: MagicMock) -> None:
        """Test donation format with verified user."""
        config = FormatConfig(donation_format="{verified}{name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_continuous)
        assert "✓LoyalDonor: Day 7!" in result

    def test_format_donation_unknown_pay_type(self, mock_donation_message_full: MagicMock) -> None:
        """Test donation format with unknown pay type preserves original value."""
        mock_donation_message_full.pay_type = "UNKNOWN_TYPE"
        config = FormatConfig(donation_format="{amount}원({pay_type}) {name}: {msg}")
        formatter = ChatFormatter(config)
        result = formatter.format_donation(mock_donation_message_full)
        assert "1000원(UNKNOWN_TYPE) Donor: Great!" in result
