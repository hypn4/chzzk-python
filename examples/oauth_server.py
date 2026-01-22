"""Chzzk OAuth Example Server.

A simple Flask server demonstrating the OAuth 2.0 authorization code flow
with the Chzzk Python SDK, including API usage examples.

Usage:
    1. Copy .env.example to .env and fill in your credentials
    2. Run: uv run python examples/oauth_server.py
    3. Open http://localhost:8080 in your browser
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, request

from chzzk import (
    ChzzkAPIError,
    ChzzkClient,
    FileTokenStorage,
    InvalidStateError,
    TokenExpiredError,
)

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Configuration
CLIENT_ID = os.environ.get("CHZZK_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CHZZK_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("CHZZK_REDIRECT_URI", "http://localhost:8080/callback")
TOKEN_FILE = Path(os.environ.get("CHZZK_TOKEN_FILE", str(Path.home() / ".chzzk_token.json")))
PORT = int(os.environ.get("CHZZK_PORT", "8080"))

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: CHZZK_CLIENT_ID and CHZZK_CLIENT_SECRET must be set")
    print("Copy examples/.env.example to examples/.env and fill in your credentials")
    exit(1)

# Initialize Flask app
app = Flask(__name__)

# Initialize Chzzk client with file-based token storage
client = ChzzkClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    token_storage=FileTokenStorage(TOKEN_FILE),
    auto_refresh=True,
)


@app.route("/")
def index() -> str:
    """Home page with login button or token info."""
    token = client.get_token()

    if token:
        # Try to get user info
        user_info_html = ""
        try:
            user = client.user.get_me()
            user_info_html = f"""
            <h3>User Info</h3>
            <p><strong>Channel ID:</strong> {user.channel_id}</p>
            <p><strong>Channel Name:</strong> {user.channel_name}</p>
            """
        except ChzzkAPIError as e:
            user_info_html = f"<p><em>Could not fetch user info: {e}</em></p>"

        return f"""
        <html>
        <head><title>Chzzk OAuth Demo</title></head>
        <body>
            <h1>Chzzk OAuth Demo</h1>
            <h2>Logged In</h2>
            {user_info_html}
            <hr>
            <h3>Token Info</h3>
            <p><strong>Access Token:</strong> {token.access_token[:20]}...</p>
            <p><strong>Token Type:</strong> {token.token_type}</p>
            <p><strong>Expires At:</strong> {token.expires_at}</p>
            <p><strong>Is Expired:</strong> {token.is_expired}</p>
            <p><strong>Scope:</strong> {token.scope or "N/A"}</p>
            <hr>
            <h3>API Demo</h3>
            <ul>
                <li><a href="/me">Get My Info (/me)</a></li>
                <li><a href="/live">Live Broadcasts (/live)</a></li>
                <li><a href="/live-setting">My Live Setting (/live-setting)</a></li>
            </ul>
            <hr>
            <a href="/refresh">Refresh Token</a> |
            <a href="/logout">Logout</a>
        </body>
        </html>
        """
    else:
        return """
        <html>
        <head><title>Chzzk OAuth Demo</title></head>
        <body>
            <h1>Chzzk OAuth Demo</h1>
            <p>Not logged in</p>
            <a href="/login">
                <button>Login with Chzzk</button>
            </a>
        </body>
        </html>
        """


@app.route("/login")
def login() -> object:
    """Redirect to Chzzk authorization page."""
    auth_url, state = client.get_authorization_url()
    print(f"Generated state: {state}")
    return redirect(auth_url)


@app.route("/callback")
def callback() -> str:
    """Handle OAuth callback and exchange code for token."""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Authorization Error</h1>
            <p>{error}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """

    if not code or not state:
        return """
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Missing Parameters</h1>
            <p>Code or state parameter is missing</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """

    try:
        token = client.authenticate(code=code, state=state)
        return f"""
        <html>
        <head><title>Success</title></head>
        <body>
            <h1>Login Successful!</h1>
            <p><strong>Access Token:</strong> {token.access_token[:20]}...</p>
            <p><strong>Refresh Token:</strong> {token.refresh_token[:20]}...</p>
            <p><strong>Expires In:</strong> {token.expires_in} seconds</p>
            <p>Token saved to: {TOKEN_FILE}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except InvalidStateError as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>State Mismatch</h1>
            <p>{e.message}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Token Exchange Error</h1>
            <p>{e!s}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """


@app.route("/refresh")
def refresh() -> str:
    """Refresh the access token."""
    try:
        token = client.refresh_token()
        return f"""
        <html>
        <head><title>Token Refreshed</title></head>
        <body>
            <h1>Token Refreshed!</h1>
            <p><strong>New Access Token:</strong> {token.access_token[:20]}...</p>
            <p><strong>Expires At:</strong> {token.expires_at}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except TokenExpiredError:
        return """
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>No Token to Refresh</h1>
            <p>Please login first</p>
            <a href="/login">Login</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Refresh Error</h1>
            <p>{e!s}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """


@app.route("/logout")
def logout() -> str:
    """Revoke the token and logout."""
    try:
        client.revoke_token()
        return """
        <html>
        <head><title>Logged Out</title></head>
        <body>
            <h1>Logged Out</h1>
            <p>Token has been revoked</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Logout Error</h1>
            <p>{e!s}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """


@app.route("/me")
def me() -> str:
    """Get the current user's information."""
    if not client.is_authenticated:
        return """
        <html>
        <head><title>Not Authenticated</title></head>
        <body>
            <h1>Not Authenticated</h1>
            <p>Please login first</p>
            <a href="/login">Login</a>
        </body>
        </html>
        """

    try:
        user = client.user.get_me()
        return f"""
        <html>
        <head><title>User Info</title></head>
        <body>
            <h1>User Info</h1>
            <p><strong>Channel ID:</strong> {user.channel_id}</p>
            <p><strong>Channel Name:</strong> {user.channel_name}</p>
            <hr>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except ChzzkAPIError as e:
        return f"""
        <html>
        <head><title>API Error</title></head>
        <body>
            <h1>API Error</h1>
            <p>{e!s}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """


@app.route("/live")
def live() -> str:
    """Get a list of live broadcasts."""
    try:
        response = client.live.get_lives(size=10)
        lives_html = ""
        for live in response.data:
            tags_str = ", ".join(live.tags) if live.tags else "None"
            lives_html += f"""
            <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                <h3>{live.live_title}</h3>
                <p><strong>Channel:</strong> {live.channel_name}</p>
                <p><strong>Viewers:</strong> {live.concurrent_user_count:,}</p>
                <p><strong>Category:</strong> {live.live_category_value or "N/A"}</p>
                <p><strong>Tags:</strong> {tags_str}</p>
            </div>
            """

        if not response.data:
            lives_html = "<p>No live broadcasts found.</p>"

        return f"""
        <html>
        <head><title>Live Broadcasts</title></head>
        <body>
            <h1>Live Broadcasts</h1>
            <p>Showing {len(response.data)} live streams</p>
            {lives_html}
            <hr>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except ChzzkAPIError as e:
        return f"""
        <html>
        <head><title>API Error</title></head>
        <body>
            <h1>API Error</h1>
            <p>{e!s}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """


@app.route("/live-setting")
def live_setting() -> str:
    """Get the current user's live broadcast setting."""
    if not client.is_authenticated:
        return """
        <html>
        <head><title>Not Authenticated</title></head>
        <body>
            <h1>Not Authenticated</h1>
            <p>Please login first</p>
            <a href="/login">Login</a>
        </body>
        </html>
        """

    try:
        setting = client.live.get_setting()
        category_html = "N/A"
        if setting.category:
            category_html = f"{setting.category.category_value} ({setting.category.category_type})"

        tags_str = ", ".join(setting.tags) if setting.tags else "None"

        return f"""
        <html>
        <head><title>Live Setting</title></head>
        <body>
            <h1>My Live Setting</h1>
            <p><strong>Default Title:</strong> {setting.default_live_title or "N/A"}</p>
            <p><strong>Category:</strong> {category_html}</p>
            <p><strong>Tags:</strong> {tags_str}</p>
            <hr>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except ChzzkAPIError as e:
        return f"""
        <html>
        <head><title>API Error</title></head>
        <body>
            <h1>API Error</h1>
            <p>{e!s}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """


if __name__ == "__main__":
    print("=" * 50)
    print("Chzzk OAuth Example Server")
    print("=" * 50)
    print(f"Client ID: {CLIENT_ID[:10]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Token File: {TOKEN_FILE}")
    print("=" * 50)
    print(f"Open http://localhost:{PORT} in your browser")
    print("=" * 50)
    app.run(host="localhost", port=PORT, debug=True)
