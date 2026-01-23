"""Chzzk Unofficial Chat Example (Sync).

비공식 API를 사용한 실시간 채팅 수신 및 전송 예제입니다.
네이버 쿠키 (NID_AUT, NID_SES)를 통한 인증이 필요합니다.

Usage:
    1. .env 파일에 네이버 쿠키 설정
    2. uv run python examples/unofficial_chat.py <channel_id>
    3. 메시지를 입력하고 Enter를 눌러 채팅 전송
    4. Ctrl+C로 종료
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

from chzzk.exceptions import ChatNotLiveError
from chzzk.unofficial import (
    ChatMessage,
    DonationMessage,
    UnofficialChatClient,
)

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Configuration
NID_AUT = os.environ.get("CHZZK_NID_AUT", "")
NID_SES = os.environ.get("CHZZK_NID_SES", "")


def get_channel_id() -> str:
    """Get channel ID from command line arguments or environment variable."""
    if len(sys.argv) > 1:
        return sys.argv[1]

    channel_id = os.environ.get("CHZZK_CHANNEL_ID", "")
    if channel_id:
        return channel_id

    print("Error: Channel ID is required")
    print("Usage: uv run python examples/unofficial_chat.py <channel_id>")
    print("Or set CHZZK_CHANNEL_ID in .env file")
    sys.exit(1)


def main() -> None:
    """Run the unofficial chat client."""
    if not NID_AUT or not NID_SES:
        print("Error: CHZZK_NID_AUT and CHZZK_NID_SES must be set")
        print("Copy examples/.env.example to examples/.env and fill in your Naver cookies")
        sys.exit(1)

    channel_id = get_channel_id()

    # Create unofficial chat client
    chat = UnofficialChatClient(
        nid_aut=NID_AUT,
        nid_ses=NID_SES,
    )

    @chat.on_chat
    def on_chat(msg: ChatMessage) -> None:
        """Handle incoming chat messages."""
        nickname = msg.profile.nickname if msg.profile else "Unknown"
        print(f"[Chat] {nickname}: {msg.content}")

    @chat.on_donation
    def on_donation(msg: DonationMessage) -> None:
        """Handle incoming donations."""
        print(f"[Donation] {msg.nickname} donated {msg.pay_amount}won: {msg.message}")

    @chat.on_system
    def on_system(data: dict) -> None:
        """Handle system events."""
        cmd = data.get("cmd")
        if cmd not in (0, 10100):  # Ignore PING and RECENT_CHAT
            print(f"[System] cmd={cmd}: {data}")

    print("=" * 50)
    print("Chzzk Unofficial Chat Example")
    print("=" * 50)
    print(f"Channel ID: {channel_id}")

    # Check if channel is live before connecting
    print("Checking live status...")
    try:
        live_detail = chat.get_live_detail(channel_id)
        if not live_detail.is_live:
            print(f"Error: Channel is not currently live (status: {live_detail.status})")
            chat.close()
            sys.exit(1)
        print(f"Channel is live: {live_detail.live_title}")
    except Exception as e:
        print(f"Error getting live detail: {e}")
        chat.close()
        sys.exit(1)

    # Connect to chat
    print("Connecting to chat...")
    try:
        chat.connect(channel_id)
        print("Connected!")
    except ChatNotLiveError:
        print("Error: Channel is not currently live")
        chat.close()
        sys.exit(1)
    except Exception as e:
        print(f"Error connecting to chat: {e}")
        chat.close()
        sys.exit(1)

    print("=" * 50)
    print("Listening for messages... (Press Ctrl+C to stop)")
    print("Type a message and press Enter to send.")
    print("=" * 50)

    # Input loop for sending messages in a separate thread
    stop_event = threading.Event()

    def input_loop() -> None:
        """Handle user input for sending messages."""
        while not stop_event.is_set():
            try:
                msg = input()
                if msg.strip():
                    chat.send_message(msg)
            except EOFError:
                break

    input_thread = threading.Thread(target=input_loop, daemon=True)
    input_thread.start()

    # Run forever until interrupted
    try:
        chat.run_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stop_event.set()
        chat.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()
