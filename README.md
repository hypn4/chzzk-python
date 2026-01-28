# chzzk-python

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Unofficial Python SDK for Chzzk (NAVER Live Streaming Platform) API

[한국어](README_KO.md)

## Installation

```bash
# Using uv (recommended)
uv add chzzk-python

# Using pip
pip install chzzk-python
```

### CLI Installation

```bash
# Using uv (recommended)
uv add "chzzk-python[cli]"

# Using pip
pip install "chzzk-python[cli]"
```

## Quick Start

```python
from chzzk import ChzzkClient, FileTokenStorage

# Create client with OAuth support
client = ChzzkClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8080/callback",
    token_storage=FileTokenStorage("token.json"),
)

# Generate authorization URL
auth_url, state = client.get_authorization_url()
# User visits auth_url and authorizes the app

# Exchange code for token (after OAuth callback)
token = client.authenticate(code="auth-code", state=state)

# Use the API
user = client.user.get_me()
print(f"Channel: {user.channel_name}")
```

## API Categories & Implementation Status

| Category | Status | Description |
|----------|--------|-------------|
| **Authorization** | ✅ Implemented | OAuth 2.0, Token issue/refresh/revoke |
| **User** | ✅ Implemented | Get logged-in user info |
| **Channel** | ✅ Implemented | Channel info, managers, followers, subscribers |
| **Category** | ✅ Implemented | Category search |
| **Live** | ✅ Implemented | Live list, stream key, broadcast settings |
| **Chat** | ✅ Implemented | Send messages, announcements, chat settings |
| **Session** | ✅ Implemented | Session create/list, event subscription |
| **Restriction** | ✅ Implemented | Activity restriction list management |
| **Drops** | ❌ Not Implemented | - |
| **Webhook Event** | ❌ Not Implemented | - |

> A [CLI](#command-line-interface) is also available for quick terminal access.

## Features

### Sync/Async Support

Both synchronous and asynchronous clients are available:

```python
# Synchronous
from chzzk import ChzzkClient

with ChzzkClient(client_id="...", client_secret="...") as client:
    user = client.user.get_me()

# Asynchronous
from chzzk import AsyncChzzkClient

async with AsyncChzzkClient(client_id="...", client_secret="...") as client:
    user = await client.user.get_me()
```

### Token Storage

Multiple token storage options:

```python
from chzzk import InMemoryTokenStorage, FileTokenStorage, CallbackTokenStorage

# In-memory (default)
storage = InMemoryTokenStorage()

# File-based persistence
storage = FileTokenStorage("token.json")

# Custom callback
storage = CallbackTokenStorage(
    get_callback=lambda: load_from_db(),
    save_callback=lambda token: save_to_db(token),
    delete_callback=lambda: delete_from_db(),
)
```

### Realtime Events

Receive chat, donation, and subscription events in realtime:

```python
from chzzk import ChzzkClient, ChatEvent, DonationEvent, SubscriptionEvent

client = ChzzkClient(...)
event_client = client.create_event_client()

@event_client.on_chat
def on_chat(event: ChatEvent):
    print(f"{event.profile.nickname}: {event.content}")

@event_client.on_donation
def on_donation(event: DonationEvent):
    print(f"{event.donator_nickname} donated {event.pay_amount}won")

@event_client.on_subscription
def on_subscription(event: SubscriptionEvent):
    print(f"{event.subscriber_nickname} subscribed!")

# Connect and subscribe
event_client.connect()
event_client.subscribe_chat()
event_client.subscribe_donation()
event_client.subscribe_subscription()
event_client.run_forever()
```

## Usage Examples

### OAuth Authentication Flow

```python
from chzzk import ChzzkClient, FileTokenStorage

client = ChzzkClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8080/callback",
    token_storage=FileTokenStorage("token.json"),
    auto_refresh=True,  # Automatically refresh expired tokens
)

# 1. Generate authorization URL
auth_url, state = client.get_authorization_url()
print(f"Visit: {auth_url}")

# 2. After user authorizes, exchange code for token
token = client.authenticate(code="received-code", state=state)

# 3. Refresh token manually if needed
new_token = client.refresh_token()

# 4. Revoke token on logout
client.revoke_token()
```

### Channel & Live Information

```python
# Get channel info
channel = client.channel.get_channel("channel-id")
print(f"Channel: {channel.channel_name}")
print(f"Description: {channel.channel_description}")

# Get followers
followers = client.channel.get_followers(size=20)
for follower in followers.data:
    print(f"Follower: {follower.nickname}")

# Get live broadcasts
lives = client.live.get_lives(size=10)
for live in lives.data:
    print(f"{live.channel_name}: {live.live_title} ({live.concurrent_user_count} viewers)")

# Get/Update live settings
setting = client.live.get_setting()
client.live.update_setting(default_live_title="My Stream Title")
```

### Chat Messages

```python
# Send chat message
client.chat.send_message(channel_id="channel-id", message="Hello!")

# Set chat announcement
client.chat.set_notice(
    channel_id="channel-id",
    message="Welcome to the stream!",
)

# Get/Update chat settings
settings = client.chat.get_settings(channel_id="channel-id")
client.chat.update_settings(
    channel_id="channel-id",
    chat_available_group="FOLLOWER",
)
```

### Async Example

```python
import asyncio
from chzzk import AsyncChzzkClient, FileTokenStorage

async def main():
    async with AsyncChzzkClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
        redirect_uri="http://localhost:8080/callback",
        token_storage=FileTokenStorage("token.json"),
    ) as client:
        # Get user info
        user = await client.user.get_me()
        print(f"Channel: {user.channel_name}")

        # Get live broadcasts
        lives = await client.live.get_lives(size=10)
        for live in lives.data:
            print(f"{live.channel_name}: {live.live_title}")

asyncio.run(main())
```

## Exception Handling

```python
from chzzk import (
    ChzzkError,              # Base exception
    ChzzkAPIError,           # API error response
    AuthenticationError,     # 401 errors
    InvalidTokenError,       # Invalid/expired token
    InvalidClientError,      # Invalid client credentials
    ForbiddenError,          # 403 errors
    NotFoundError,           # 404 errors
    RateLimitError,          # 429 errors
    ServerError,             # 5xx errors
    TokenExpiredError,       # Token expired, need re-auth
    InvalidStateError,       # OAuth state mismatch
    SessionError,            # Session-related errors
    SessionConnectionError,  # Socket.IO connection failed
    SessionLimitExceededError,  # Max session limit exceeded
    EventSubscriptionError,  # Event subscription failed
)

try:
    user = client.user.get_me()
except InvalidTokenError:
    # Token is invalid or expired
    token = client.refresh_token()
except RateLimitError:
    # Rate limit exceeded, wait and retry
    time.sleep(60)
except ChzzkAPIError as e:
    print(f"API Error: [{e.status_code}] {e.error_code}: {e.message}")
```

## Unofficial API

In addition to the official API, we provide an unofficial API using Naver cookie authentication.
This enables real-time chat receiving/sending functionality.

> ⚠️ The unofficial API may change at any time and is not officially supported.

### Unofficial Chat Client

**Synchronous version:**

```python
from chzzk.unofficial import UnofficialChatClient, ChatMessage

chat = UnofficialChatClient(
    nid_aut="your-nid-aut-cookie",
    nid_ses="your-nid-ses-cookie",
)

@chat.on_chat
def on_chat(msg: ChatMessage):
    print(f"{msg.nickname}: {msg.content}")

@chat.on_donation
def on_donation(msg):
    print(f"{msg.nickname} donated {msg.pay_amount}won")

chat.connect("channel-id")
chat.send_message("Hello!")
chat.run_forever()
```

**Asynchronous version:**

```python
from chzzk.unofficial import AsyncUnofficialChatClient, ChatMessage

async with AsyncUnofficialChatClient(
    nid_aut="your-nid-aut-cookie",
    nid_ses="your-nid-ses-cookie",
) as chat:
    @chat.on_chat
    async def on_chat(msg: ChatMessage):
        print(f"{msg.nickname}: {msg.content}")

    await chat.connect("channel-id")
    await chat.send_message("Hello!")
    await chat.run_forever()
```

### How to Get Naver Cookies

1. Log in to Naver
2. Browser Developer Tools (F12) → Application → Cookies
3. Copy `NID_AUT` and `NID_SES` cookie values

### Unofficial API Exception Handling

```python
from chzzk import ChatConnectionError, ChatNotLiveError

try:
    chat.connect("channel-id")
except ChatNotLiveError:
    print("Channel is not currently live")
except ChatConnectionError as e:
    print(f"Connection failed: {e}")
```

## Command Line Interface

A CLI is available for quick access to the unofficial API features.

### Authentication

```bash
# Login via Naver QR code (recommended)
chzzk auth qr

# Login via Naver QR code with custom timeout
chzzk auth qr --timeout 60

# Save your Naver cookies manually (interactive)
chzzk auth login

# Check authentication status
chzzk auth status

# Remove stored cookies
chzzk auth logout
```

Cookies are stored in `~/.chzzk/cookies.json`.

### Live Status

```bash
# Get detailed live information
chzzk live info CHANNEL_ID

# Get simple LIVE/OFFLINE status
chzzk live status CHANNEL_ID

# JSON output
chzzk --json live info CHANNEL_ID
```

### Chat

```bash
# Watch real-time chat
chzzk chat watch CHANNEL_ID

# Watch chat even when offline
chzzk chat watch CHANNEL_ID --offline

# Save chat to file
chzzk chat watch CHANNEL_ID --output chat.jsonl
chzzk chat watch CHANNEL_ID --output chat.txt --output-format txt

# Auto-generate filename based on stream info (recommended)
# Creates: {channel_id}_{live_id}_{YYYYMMDD}.jsonl
chzzk chat watch CHANNEL_ID --output-dir ./logs

# Send a single message (requires authentication)
chzzk chat send CHANNEL_ID "Hello!"

# Send to offline channel
chzzk chat send CHANNEL_ID "Hello!" --offline

# Interactive mode: send and receive messages
chzzk chat send CHANNEL_ID --interactive
# or
chzzk chat send CHANNEL_ID -i

# Interactive mode with chat logging
chzzk chat send CHANNEL_ID -i --output-dir ./logs

# Interactive mode with offline channel
chzzk chat send CHANNEL_ID -i --offline
```

### Global Options

```bash
--nid-aut TEXT      # Override NID_AUT cookie (env: CHZZK_NID_AUT)
--nid-ses TEXT      # Override NID_SES cookie (env: CHZZK_NID_SES)
--json              # Output in JSON format
--log-level LEVEL   # Set log level (DEBUG, INFO, WARNING, ERROR)
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `CHZZK_NID_AUT` | NID_AUT cookie value |
| `CHZZK_NID_SES` | NID_SES cookie value |
| `CHZZK_LOG_LEVEL` | Default log level |
| `CHZZK_CHAT_OUTPUT` | Default chat output file path |
| `CHZZK_CHAT_OUTPUT_DIR` | Default chat output directory (auto-generates filename) |
| `CHZZK_CHAT_OUTPUT_FORMAT` | Default chat output format (jsonl, txt) |

## Examples

See the [examples](examples/) directory for complete working examples:

- `oauth_server.py` - OAuth authentication with Flask
- `realtime_chat.py` - Realtime chat/donation/subscription events (sync)
- `realtime_chat_async.py` - Realtime events (async)
- `session_management.py` - Session management example
- `unofficial_chat.py` - Unofficial chat client (sync)
- `unofficial_chat_async.py` - Unofficial chat client (async)

## API Reference

For detailed API documentation, see the [Official Chzzk API Documentation](https://chzzk.gitbook.io/chzzk).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is an unofficial SDK and is not affiliated with NAVER or Chzzk. Use at your own risk.
