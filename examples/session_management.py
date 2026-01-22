"""Chzzk Session Management Example.

세션 REST API를 사용하여 세션을 관리하는 예제입니다.

Usage:
    1. .env 파일에 인증 정보 설정
    2. uv run python examples/session_management.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from chzzk import ChzzkClient, FileTokenStorage

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


def show_sessions_user() -> None:
    """Show sessions created with user authentication."""
    print("\n--- User Sessions (Access Token Auth) ---")

    if not client.is_authenticated:
        print("Not authenticated. Please run oauth_server.py first.")
        return

    sessions = client.session.get_sessions()

    if not sessions:
        print("No active sessions.")
        return

    for session in sessions:
        print(f"\nSession Key: {session.session_key}")
        print(f"  Connected: {session.connected_date}")
        print(f"  Disconnected: {session.disconnected_date or 'Still connected'}")
        print(f"  Subscribed Events: {len(session.subscribed_events)}")
        for event in session.subscribed_events:
            print(f"    - {event.event_type} (Channel: {event.channel_id})")


def show_sessions_client() -> None:
    """Show sessions created with client authentication."""
    print("\n--- Client Sessions (Client Credentials Auth) ---")

    sessions = client.session.get_client_sessions()

    if not sessions:
        print("No active client sessions.")
        return

    for session in sessions:
        print(f"\nSession Key: {session.session_key}")
        print(f"  Connected: {session.connected_date}")
        print(f"  Disconnected: {session.disconnected_date or 'Still connected'}")
        print(f"  Subscribed Events: {len(session.subscribed_events)}")
        for event in session.subscribed_events:
            print(f"    - {event.event_type} (Channel: {event.channel_id})")


def create_session_demo() -> None:
    """Demonstrate session creation."""
    print("\n--- Session Creation Demo ---")

    # User session (requires access token)
    if client.is_authenticated:
        print("\nCreating user session...")
        response = client.session.create_session()
        print(f"User Session URL: {response.url}")
    else:
        print("\nSkipping user session (not authenticated)")

    # Client session (uses client credentials)
    print("\nCreating client session...")
    response = client.session.create_client_session()
    print(f"Client Session URL: {response.url}")


def main() -> None:
    """Run the session management demo."""
    print("=" * 50)
    print("Chzzk Session Management Example")
    print("=" * 50)

    # Show existing sessions
    show_sessions_user()
    show_sessions_client()

    # Create session demo
    create_session_demo()

    # Show sessions again after creation
    print("\n--- Sessions after creation ---")
    show_sessions_user()
    show_sessions_client()

    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
