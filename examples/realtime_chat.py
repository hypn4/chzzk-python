"""Chzzk Realtime Chat Example (Sync).

실시간으로 채팅, 후원, 구독 이벤트를 수신하는 예제입니다.

Usage:
    1. .env 파일에 인증 정보 설정
    2. uv run python examples/realtime_chat.py
    3. Ctrl+C로 종료
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from chzzk import (
    ChatEvent,
    ChzzkClient,
    DonationEvent,
    FileTokenStorage,
    SubscriptionEvent,
    SystemEvent,
)

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Configuration
CLIENT_ID = os.environ.get("CHZZK_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CHZZK_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("CHZZK_REDIRECT_URI", "http://localhost:8080/callback")
TOKEN_FILE = Path(os.environ.get("CHZZK_TOKEN_FILE", str(Path.home() / ".chzzk_token.json")))

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: CHZZK_CLIENT_ID and CHZZK_CLIENT_SECRET must be set")
    print("Copy examples/.env.example to examples/.env and fill in your credentials")
    exit(1)

# Initialize Chzzk client
client = ChzzkClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    token_storage=FileTokenStorage(TOKEN_FILE),
    auto_refresh=True,
)

# Check authentication
if not client.is_authenticated:
    print("Error: Not authenticated. Please run oauth_server.py first to authenticate.")
    exit(1)

# Create event client
event_client = client.create_event_client()


@event_client.on_chat
def on_chat(event: ChatEvent) -> None:
    """Handle incoming chat messages."""
    role = f"[{event.user_role_code or 'unknown'}]"
    nickname = event.profile.nickname
    content = event.content
    print(f"[Chat] {role} {nickname}: {content}")


@event_client.on_donation
def on_donation(event: DonationEvent) -> None:
    """Handle incoming donations."""
    nickname = event.donator_nickname
    amount = event.pay_amount
    message = event.donation_text
    dtype = event.donation_type
    print(f"[Donation/{dtype}] {nickname} donated {amount}won: {message}")


@event_client.on_subscription
def on_subscription(event: SubscriptionEvent) -> None:
    """Handle incoming subscriptions."""
    nickname = event.subscriber_nickname
    month = event.month
    tier = event.tier_name
    print(f"[Subscription] {nickname} subscribed for {month} months ({tier})")


@event_client.on_system
def on_system(event: SystemEvent) -> None:
    """Handle system events."""
    print(f"[System] {event.type}: {event.data}")


def main() -> None:
    """Run the realtime chat client."""
    print("=" * 50)
    print("Chzzk Realtime Chat Example")
    print("=" * 50)

    # Connect to the event server
    print("Connecting to event server...")
    session_key = event_client.connect()
    print(f"Connected! Session key: {session_key}")

    # Subscribe to events
    print("Subscribing to events...")
    event_client.subscribe_chat()
    event_client.subscribe_donation()
    event_client.subscribe_subscription()
    print("Subscribed to chat, donation, and subscription events")

    print("=" * 50)
    print("Listening for events... (Press Ctrl+C to stop)")
    print("=" * 50)

    # Run forever until interrupted
    try:
        event_client.run_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        event_client.disconnect()
        client.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()
