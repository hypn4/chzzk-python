"""Chat message formatter for CLI output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rich.markup import escape

from chzzk.cli import timezone as tz

if TYPE_CHECKING:
    from chzzk.unofficial import ChatMessage, ChatProfile, DonationMessage

# user_role_code 매핑
ROLE_DISPLAY_MAP: dict[str, str] = {
    "streamer": "스트리머",
    "streaming_channel_manager": "매니저",
    "streaming_chat_manager": "채팅 매니저",
    "common_user": "",
}

# pay_type 매핑
PAY_TYPE_DISPLAY_MAP: dict[str, str] = {
    "CURRENCY": "현금",
    "CHEESE": "치즈",
}

# donation_type 매핑
DONATION_TYPE_DISPLAY_MAP: dict[str, str] = {
    "CHAT": "채팅",
    "VIDEO": "영상",
}


@dataclass
class FormatConfig:
    """Configuration for chat message formatting.

    Template variables (공통):
        - {time}: 로컬 타임스탬프
        - {server_time}: 서버 타임스탬프
        - {badge}: 배지 이름 (없으면 빈 문자열)
        - {name}: 닉네임
        - {msg}: 메시지 내용
        - {verified}: 인증 마크 (✓ 또는 빈 문자열)
        - {role}: 사용자 역할 (스트리머, 매니저 등)

    Template variables (donation 전용):
        - {amount}: 후원 금액
        - {pay_type}: 결제 타입 (치즈, 현금)
        - {donation_type}: 후원 타입 (채팅, 영상)
        - {continuous_days}: 연속 후원 일수 (없으면 빈 문자열)

    Template variables (system only):
        - {style}: Dynamic style

    All templates support Rich markup for styling.
    """

    chat_format: str = "[dim]{time}[/dim] {badge}[cyan]{name}[/cyan]: {msg}"
    donation_format: str = (
        "[dim]{time}[/dim] [yellow]{amount}원[/yellow] {badge}[magenta]{name}[/magenta]: {msg}"
    )
    sent_format: str = "[dim]{time}[/dim] [green bold]>[/green bold] [green]{msg}[/green]"
    system_format: str = "[dim]{time}[/dim] [{style}]{msg}[/{style}]"
    time_format: str = "%H:%M:%S"
    badge_format: str = "[{badge}] "

    @classmethod
    def from_env_and_cli(
        cls,
        *,
        cli_chat_format: str | None = None,
        cli_donation_format: str | None = None,
        cli_sent_format: str | None = None,
        cli_time_format: str | None = None,
        env_chat_format: str | None = None,
        env_donation_format: str | None = None,
        env_sent_format: str | None = None,
        env_time_format: str | None = None,
    ) -> FormatConfig:
        """Create FormatConfig from CLI options and environment variables.

        CLI options take precedence over environment variables.

        Args:
            cli_chat_format: CLI --chat-format option.
            cli_donation_format: CLI --donation-format option.
            cli_sent_format: CLI --sent-format option.
            cli_time_format: CLI --time-format option.
            env_chat_format: CHZZK_CHAT_FORMAT environment variable.
            env_donation_format: CHZZK_DONATION_FORMAT environment variable.
            env_sent_format: CHZZK_SENT_FORMAT environment variable.
            env_time_format: CHZZK_TIME_FORMAT environment variable.

        Returns:
            FormatConfig with merged settings.
        """
        defaults = cls()

        return cls(
            chat_format=cli_chat_format or env_chat_format or defaults.chat_format,
            donation_format=cli_donation_format or env_donation_format or defaults.donation_format,
            sent_format=cli_sent_format or env_sent_format or defaults.sent_format,
            time_format=cli_time_format or env_time_format or defaults.time_format,
        )


class ChatFormatter:
    """Formatter for chat messages with template support."""

    def __init__(self, config: FormatConfig | None = None) -> None:
        """Initialize the formatter.

        Args:
            config: Format configuration. Uses defaults if None.
        """
        self.config = config or FormatConfig()

    def _get_timestamp(self) -> str:
        """Get formatted timestamp string."""
        return tz.now().strftime(self.config.time_format)

    def _escape_markup(self, text: str) -> str:
        """Escape Rich markup characters in text.

        Args:
            text: Text that may contain Rich markup characters.

        Returns:
            Escaped text safe for Rich markup.
        """
        return escape(text)

    def _get_badge_str_from_profile(self, profile: ChatProfile | None) -> str:
        """Get formatted badge string from a profile.

        Args:
            profile: Chat profile with optional badge.

        Returns:
            Formatted badge string or empty string.
        """
        if not profile:
            return ""

        badge_name = None

        # 1. Check profile.badge dict
        if profile.badge:
            badge_name = profile.badge.get("name") or profile.badge.get("title")

        # 2. Check activity_badges list
        if not badge_name and profile.activity_badges:
            for activity_badge in profile.activity_badges:
                if isinstance(activity_badge, dict):
                    badge_name = (
                        activity_badge.get("name")
                        or activity_badge.get("title")
                        or activity_badge.get("badgeName")
                    )
                    if badge_name:
                        break

        if badge_name:
            return self.config.badge_format.format(badge=self._escape_markup(badge_name))
        return ""

    def _get_badge_str(self, msg: ChatMessage) -> str:
        """Get formatted badge string from a chat message.

        Args:
            msg: Chat message with optional badge.

        Returns:
            Formatted badge string or empty string.
        """
        return self._get_badge_str_from_profile(msg.profile)

    def _get_verified_str(self, profile: ChatProfile | None) -> str:
        """Get verified mark string.

        Args:
            profile: Chat profile with optional verified mark.

        Returns:
            Verified mark (✓) or empty string.
        """
        if profile and profile.verified_mark:
            return "✓"
        return ""

    def _get_role_str(self, profile: ChatProfile | None) -> str:
        """Get user role display string.

        Args:
            profile: Chat profile with optional role.

        Returns:
            Role display string (스트리머, 매니저 등) or empty string.
        """
        if not profile or not profile.user_role_code:
            return ""
        return ROLE_DISPLAY_MAP.get(profile.user_role_code, "")

    def _get_server_time_str(self, message_time: int | None) -> str:
        """Get server timestamp string.

        Args:
            message_time: Server timestamp in milliseconds.

        Returns:
            Formatted time string or empty string if not available.
        """
        if not message_time:
            return ""
        dt = tz.from_timestamp(message_time / 1000)
        return dt.strftime(self.config.time_format)

    def _get_pay_type_str(self, pay_type: str | None) -> str:
        """Get payment type display string.

        Args:
            pay_type: Payment type code (CURRENCY, CHEESE).

        Returns:
            Payment type display string (현금, 치즈) or original value.
        """
        if not pay_type:
            return ""
        return PAY_TYPE_DISPLAY_MAP.get(pay_type, pay_type)

    def _get_donation_type_str(self, donation_type: str | None) -> str:
        """Get donation type display string.

        Args:
            donation_type: Donation type code (CHAT, VIDEO).

        Returns:
            Donation type display string (채팅, 영상) or original value.
        """
        if not donation_type:
            return ""
        return DONATION_TYPE_DISPLAY_MAP.get(donation_type, donation_type)

    def _get_continuous_days_str(self, extras: dict[str, Any] | None) -> str:
        """Get continuous donation days string.

        Args:
            extras: Donation extras dictionary.

        Returns:
            Formatted days string (e.g., "7일") or empty string.
        """
        if not extras:
            return ""
        days = extras.get("continuousDonationDays")
        if days and days > 0:
            return f"{days}일"
        return ""

    def format_chat(self, msg: ChatMessage) -> str:
        """Format a chat message for console display.

        Args:
            msg: Chat message to format.

        Returns:
            Formatted string with Rich markup.
        """
        return self.config.chat_format.format(
            time=self._get_timestamp(),
            server_time=self._get_server_time_str(msg.message_time),
            badge=self._get_badge_str(msg),
            name=self._escape_markup(msg.nickname or ""),
            msg=self._escape_markup(msg.content or ""),
            verified=self._get_verified_str(msg.profile),
            role=self._get_role_str(msg.profile),
        )

    def format_donation(self, msg: DonationMessage) -> str:
        """Format a donation message for console display.

        Args:
            msg: Donation message to format.

        Returns:
            Formatted string with Rich markup.
        """
        return self.config.donation_format.format(
            time=self._get_timestamp(),
            server_time=self._get_server_time_str(msg.message_time),
            amount=msg.pay_amount,
            badge=self._get_badge_str_from_profile(msg.profile),
            name=self._escape_markup(msg.nickname or ""),
            msg=self._escape_markup(msg.content or ""),
            verified=self._get_verified_str(msg.profile),
            role=self._get_role_str(msg.profile),
            pay_type=self._get_pay_type_str(msg.pay_type),
            donation_type=self._get_donation_type_str(msg.donation_type),
            continuous_days=self._get_continuous_days_str(msg.extras),
        )

    def format_sent(self, content: str) -> str:
        """Format a sent message for console display.

        Args:
            content: Message content that was sent.

        Returns:
            Formatted string with Rich markup.
        """
        return self.config.sent_format.format(
            time=self._get_timestamp(),
            msg=self._escape_markup(content),
        )

    def format_system(self, content: str, style: str = "yellow") -> str:
        """Format a system message for console display.

        Args:
            content: System message content.
            style: Rich style name for the message.

        Returns:
            Formatted string with Rich markup.
        """
        return self.config.system_format.format(
            time=self._get_timestamp(),
            msg=self._escape_markup(content),
            style=style,
        )
