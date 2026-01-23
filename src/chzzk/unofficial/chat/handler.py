"""Message handler for unofficial chat WebSocket."""

from __future__ import annotations

import json
from typing import Any

from chzzk.unofficial.models.chat import (
    ChatCmd,
    ChatMessage,
    ChatProfile,
    DonationMessage,
)


class ChatHandler:
    """Handler for parsing and processing chat WebSocket messages."""

    @staticmethod
    def parse_message(raw_data: str | bytes) -> dict[str, Any]:
        """Parse raw WebSocket message.

        Args:
            raw_data: Raw message data.

        Returns:
            Parsed message dictionary.
        """
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        return json.loads(raw_data)

    @staticmethod
    def get_command(data: dict[str, Any]) -> ChatCmd | None:
        """Get command type from message.

        Args:
            data: Parsed message data.

        Returns:
            ChatCmd enum value or None.
        """
        cmd = data.get("cmd")
        if cmd is not None:
            try:
                return ChatCmd(cmd)
            except ValueError:
                return None
        return None

    @staticmethod
    def parse_chat_messages(data: dict[str, Any]) -> list[ChatMessage]:
        """Parse chat messages from body.

        Args:
            data: Parsed message data with body.

        Returns:
            List of ChatMessage objects.
        """
        messages = []
        body = data.get("bdy", [])

        if isinstance(body, list):
            for item in body:
                try:
                    # Parse profile from JSON string if present
                    profile_str = item.get("profile")
                    if profile_str and isinstance(profile_str, str):
                        profile_data = json.loads(profile_str)
                        item["profile"] = ChatProfile.model_validate(profile_data)
                    elif profile_str and isinstance(profile_str, dict):
                        item["profile"] = ChatProfile.model_validate(profile_str)

                    # Parse extras from JSON string if present
                    extras_str = item.get("extras")
                    if extras_str and isinstance(extras_str, str):
                        item["extras"] = json.loads(extras_str)

                    messages.append(ChatMessage.model_validate(item))
                except Exception:
                    # Skip malformed messages
                    continue

        return messages

    @staticmethod
    def parse_donation_messages(data: dict[str, Any]) -> list[DonationMessage]:
        """Parse donation messages from body.

        Args:
            data: Parsed message data with body.

        Returns:
            List of DonationMessage objects.
        """
        messages = []
        body = data.get("bdy", [])

        if isinstance(body, list):
            for item in body:
                try:
                    # Parse profile from JSON string if present
                    profile_str = item.get("profile")
                    if profile_str and isinstance(profile_str, str):
                        profile_data = json.loads(profile_str)
                        item["profile"] = ChatProfile.model_validate(profile_data)
                    elif profile_str and isinstance(profile_str, dict):
                        item["profile"] = ChatProfile.model_validate(profile_str)

                    # Parse extras from JSON string if present
                    extras_str = item.get("extras")
                    if extras_str and isinstance(extras_str, str):
                        item["extras"] = json.loads(extras_str)

                    messages.append(DonationMessage.model_validate(item))
                except Exception:
                    # Skip malformed messages
                    continue

        return messages

    @staticmethod
    def create_connect_message(
        chat_channel_id: str,
        access_token: str,
        *,
        uid: str | None = None,
        service_id: str = "game",
        protocol_version: str = "3",
    ) -> str:
        """Create connection message for WebSocket.

        Args:
            chat_channel_id: Chat channel ID.
            access_token: Chat access token.
            uid: User ID hash for authenticated connections (enables chat sending).
            service_id: Service ID (default: "game").
            protocol_version: Protocol version (default: "3").

        Returns:
            JSON string of connect message.
        """
        message = {
            "cmd": ChatCmd.CONNECT,
            "ver": protocol_version,
            "svcid": service_id,
            "cid": chat_channel_id,
            "bdy": {
                "uid": uid,
                "devType": 2001,
                "accTkn": access_token,
                "auth": "SEND" if uid else "READ",
            },
            "tid": 1,
        }
        return json.dumps(message)

    @staticmethod
    def create_send_chat_message(
        chat_channel_id: str,
        content: str,
        *,
        session_id: str,
        extra_token: str,
        streaming_channel_id: str,
        extras: dict[str, Any] | None = None,
        service_id: str = "game",
        protocol_version: str = "3",
    ) -> str:
        """Create chat send message for WebSocket.

        Args:
            chat_channel_id: Chat channel ID.
            content: Message content.
            session_id: WebSocket session ID (from CONNECTED response).
            extra_token: Extra token from access-token API.
            streaming_channel_id: Streaming channel ID.
            extras: Optional extra data to merge.
            service_id: Service ID (default: "game").
            protocol_version: Protocol version (default: "3").

        Returns:
            JSON string of send message.
        """
        import time

        default_extras = {
            "chatType": "STREAMING",
            "osType": "PC",
            "extraToken": extra_token,
            "streamingChannelId": streaming_channel_id,
            "emojis": {},
        }
        if extras:
            default_extras.update(extras)

        body = {
            "msg": content,
            "msgTypeCode": 1,
            "extras": json.dumps(default_extras),
            "msgTime": int(time.time() * 1000),
        }

        message = {
            "cmd": ChatCmd.SEND_CHAT,
            "ver": protocol_version,
            "svcid": service_id,
            "cid": chat_channel_id,
            "sid": session_id,
            "bdy": body,
            "tid": 2,
            "retry": False,
        }
        return json.dumps(message)

    @staticmethod
    def create_pong_message() -> str:
        """Create pong message for keepalive.

        Returns:
            JSON string of pong message.
        """
        return json.dumps({"cmd": ChatCmd.PONG, "ver": "3"})

    @staticmethod
    def create_recent_chat_request(
        chat_channel_id: str,
        *,
        service_id: str = "game",
        protocol_version: str = "3",
    ) -> str:
        """Create request for recent chat messages.

        Args:
            chat_channel_id: Chat channel ID.
            service_id: Service ID (default: "game").
            protocol_version: Protocol version (default: "3").

        Returns:
            JSON string of recent chat request.
        """
        message = {
            "cmd": ChatCmd.REQUEST_RECENT_CHAT,
            "ver": protocol_version,
            "svcid": service_id,
            "cid": chat_channel_id,
            "sid": 1,
            "bdy": {"recentMessageCount": 50},
            "tid": 3,
        }
        return json.dumps(message)
