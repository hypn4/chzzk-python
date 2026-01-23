"""Chzzk Unofficial Chat Example (Async).

비동기 방식으로 비공식 API를 사용한 채팅 수신 및 전송 예제입니다.
네이버 쿠키 (NID_AUT, NID_SES)를 통한 인증이 필요합니다.

Usage:
    1. .env 파일에 네이버 쿠키 설정
    2. uv run python examples/unofficial_chat_async.py <channel_id>
    3. 메시지를 입력하고 Enter를 눌러 채팅 전송
    4. Ctrl+C로 종료
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from chzzk.exceptions import ChatNotLiveError
from chzzk.unofficial import (
    AsyncUnofficialChatClient,
    ChatMessage,
    DonationMessage,
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
    print("Usage: uv run python examples/unofficial_chat_async.py <channel_id>")
    print("Or set CHZZK_CHANNEL_ID in .env file")
    sys.exit(1)


async def main() -> None:
    """Run the async unofficial chat client."""
    if not NID_AUT or not NID_SES:
        print("Error: CHZZK_NID_AUT and CHZZK_NID_SES must be set")
        print("Copy examples/.env.example to examples/.env and fill in your Naver cookies")
        sys.exit(1)

    channel_id = get_channel_id()

    async with AsyncUnofficialChatClient(
        nid_aut=NID_AUT,
        nid_ses=NID_SES,
    ) as chat:

        @chat.on_chat
        async def on_chat(msg: ChatMessage) -> None:
            """Handle incoming chat messages."""
            nickname = msg.profile.nickname if msg.profile else "Unknown"
            print(f"[Chat] {nickname}: {msg.content}")

        @chat.on_donation
        async def on_donation(msg: DonationMessage) -> None:
            """Handle incoming donations."""
            print(f"[Donation] {msg.nickname} donated {msg.pay_amount}won: {msg.message}")

        @chat.on_system
        async def on_system(data: dict) -> None:
            """Handle system events."""
            cmd = data.get("cmd")
            if cmd not in (0, 10100):  # Ignore PING and RECENT_CHAT
                print(f"[System] cmd={cmd}: {data}")

        print("=" * 50)
        print("Chzzk Unofficial Chat Example (Async)")
        print("=" * 50)
        print(f"Channel ID: {channel_id}")

        # Check if channel is live before connecting
        print("Checking live status...")
        try:
            live_detail = await chat.get_live_detail(channel_id)
            if not live_detail.is_live:
                print(f"Error: Channel is not currently live (status: {live_detail.status})")
                return
            print(f"Channel is live: {live_detail.live_title}")
        except Exception as e:
            print(f"Error getting live detail: {e}")
            return

        # Connect to chat
        print("Connecting to chat...")
        try:
            await chat.connect(channel_id)
            print("Connected!")
        except ChatNotLiveError:
            print("Error: Channel is not currently live")
            return
        except Exception as e:
            print(f"Error connecting to chat: {e}")
            return

        print("=" * 50)
        print("Listening for messages... (Press Ctrl+C to stop)")
        print("Type a message and press Enter to send.")
        print("=" * 50)

        # Input task for sending messages
        async def input_task() -> None:
            """Handle user input for sending messages."""
            loop = asyncio.get_event_loop()
            while True:
                try:
                    msg = await loop.run_in_executor(None, input)
                    if msg.strip():
                        await chat.send_message(msg)
                except EOFError:
                    break

        # Run input task and chat listener concurrently
        input_coro = input_task()
        chat_coro = chat.run_forever()

        try:
            await asyncio.gather(input_coro, chat_coro)
        except asyncio.CancelledError:
            print("\nStopping...")
        finally:
            print("Disconnected.")


if __name__ == "__main__":
    import contextlib

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
