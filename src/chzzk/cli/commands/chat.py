"""Chat commands for CLI."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import signal
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console

from chzzk.constants import StatusText
from chzzk.exceptions import ChatConnectionError, ChatNotLiveError
from chzzk.unofficial import (
    AsyncUnofficialChzzkClient,
    ChatMessage,
    DonationMessage,
    UnofficialChzzkClient,
)

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = logging.getLogger("chzzk.cli.chat")


def get_config(ctx: typer.Context) -> ConfigManager:
    """Get ConfigManager from context."""
    return ctx.obj["config"]


def get_auth_cookies(ctx: typer.Context) -> tuple[str | None, str | None]:
    """Get authentication cookies from context."""
    config = get_config(ctx)
    return config.get_auth_cookies(
        cli_nid_aut=ctx.obj.get("nid_aut"),
        cli_nid_ses=ctx.obj.get("nid_ses"),
    )


def format_chat_message(msg: ChatMessage, json_output: bool = False) -> str:
    """Format a chat message for display."""
    if json_output:
        return json.dumps(
            {
                "type": "chat",
                "timestamp": datetime.now().isoformat(),
                "user_id_hash": msg.user_id_hash,
                "nickname": msg.nickname,
                "content": msg.content,
                "badge": (
                    msg.profile.badge.get("name") if msg.profile and msg.profile.badge else None
                ),
            }
        )

    timestamp = datetime.now().strftime("%H:%M:%S")
    badge = ""
    if msg.profile and msg.profile.badge:
        badge = f"[{msg.profile.badge.get('name')}] " if msg.profile.badge.get("name") else ""

    return f"[dim]{timestamp}[/dim] {badge}[cyan]{msg.nickname}[/cyan]: {msg.content}"


def format_donation_message(msg: DonationMessage, json_output: bool = False) -> str:
    """Format a donation message for display."""
    if json_output:
        return json.dumps(
            {
                "type": "donation",
                "timestamp": datetime.now().isoformat(),
                "user_id_hash": msg.user_id_hash,
                "nickname": msg.nickname,
                "content": msg.content,
                "pay_amount": msg.pay_amount,
            }
        )

    timestamp = datetime.now().strftime("%H:%M:%S")
    return (
        f"[dim]{timestamp}[/dim] [yellow]${msg.pay_amount}[/yellow] "
        f"[magenta]{msg.nickname}[/magenta]: {msg.content or ''}"
    )


@app.command()
def watch(
    ctx: typer.Context,
    channel_id: Annotated[
        str,
        typer.Argument(help="Channel ID to watch chat for"),
    ],
    offline: Annotated[
        bool,
        typer.Option(
            "--offline",
            help="Connect to chat even when channel is offline",
        ),
    ] = False,
) -> None:
    """Watch real-time chat messages from a channel.

    By default, only connects when the channel is live.
    Use --offline to connect to chat even when offline.
    """
    nid_aut, nid_ses = get_auth_cookies(ctx)
    json_output = ctx.obj.get("json_output", False)

    async def run_chat() -> None:
        async with AsyncUnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
            chat = client.create_chat_client()

            @chat.on_chat
            async def handle_chat(msg: ChatMessage) -> None:
                console.print(format_chat_message(msg, json_output))

            @chat.on_donation
            async def handle_donation(msg: DonationMessage) -> None:
                console.print(format_donation_message(msg, json_output))

            # Get live detail first to check status
            try:
                live_detail = await client.live.get_live_detail(channel_id)
            except Exception as e:
                logger.error(f"Failed to get live detail: {e}")
                if json_output:
                    console.print(json.dumps({"error": str(e)}))
                else:
                    console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from None

            # Connect to chat
            try:
                if not json_output:
                    status_text = StatusText.LIVE if live_detail.is_live else StatusText.OFFLINE
                    console.print(
                        f"[green]Connecting to chat...[/green] "
                        f"({live_detail.channel_name or channel_id} - {status_text})"
                    )

                await chat.connect(channel_id, allow_offline=offline)

                if not json_output:
                    console.print(
                        f"[green]Connected![/green] Watching chat for "
                        f"[cyan]{live_detail.channel_name or channel_id}[/cyan]"
                    )
                    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

            except ChatNotLiveError:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "error": "Channel is not live",
                                "channel_id": channel_id,
                                "hint": "Use --offline to connect anyway",
                            }
                        )
                    )
                else:
                    console.print(
                        f"[yellow]Channel {channel_id} is not live.[/yellow]\n"
                        f"Use [cyan]--offline[/cyan] to connect to chat anyway."
                    )
                raise typer.Exit(1) from None

            except ChatConnectionError as e:
                logger.error(f"Failed to connect to chat: {e}")
                if json_output:
                    console.print(json.dumps({"error": str(e)}))
                else:
                    console.print(f"[red]Connection error:[/red] {e}")
                raise typer.Exit(1) from None

            # Handle graceful shutdown
            loop = asyncio.get_running_loop()
            stop_event = asyncio.Event()

            def signal_handler() -> None:
                stop_event.set()
                chat.stop()

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)

            try:
                await chat.run_forever()
            except asyncio.CancelledError:
                pass
            finally:
                if not json_output:
                    console.print("\n[yellow]Disconnected[/yellow]")

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_chat())


def format_sent_message(content: str, json_output: bool = False) -> str:
    """Format a sent message for display."""
    if json_output:
        return json.dumps(
            {
                "type": "sent",
                "timestamp": datetime.now().isoformat(),
                "content": content,
            }
        )

    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[dim]{timestamp}[/dim] [green bold]>[/green bold] [green]{content}[/green]"


@app.command()
def send(
    ctx: typer.Context,
    channel_id: Annotated[
        str,
        typer.Argument(help="Channel ID to send message to"),
    ],
    message: Annotated[
        str | None,
        typer.Argument(help="Message to send (not required in interactive mode)"),
    ] = None,
    offline: Annotated[
        bool,
        typer.Option(
            "--offline",
            help="Connect to chat even when channel is offline",
        ),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Interactive chat mode (send and receive messages)",
        ),
    ] = False,
) -> None:
    """Send a chat message to a channel.

    Requires authentication (NID_AUT and NID_SES cookies).

    By default, sends a single message and exits. Use --interactive for
    a persistent connection where you can send and receive messages.
    Use --offline to connect even when the channel is offline.
    """
    nid_aut, nid_ses = get_auth_cookies(ctx)
    json_output = ctx.obj.get("json_output", False)

    if not nid_aut or not nid_ses:
        if json_output:
            console.print(json.dumps({"error": "Authentication required"}))
        else:
            console.print(
                "[red]Error:[/red] Authentication required to send messages.\n"
                "Run [cyan]chzzk auth login[/cyan] to save your cookies."
            )
        raise typer.Exit(1)

    # Validate arguments
    if not interactive and not message:
        if json_output:
            console.print(json.dumps({"error": "Message required in non-interactive mode"}))
        else:
            console.print(
                "[red]Error:[/red] Message is required.\n"
                "Use [cyan]--interactive[/cyan] for interactive mode."
            )
        raise typer.Exit(1)

    if interactive:
        _run_interactive_chat(
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            offline=offline,
            json_output=json_output,
        )
    else:
        # message is guaranteed to be non-None here (checked above)
        assert message is not None
        _send_single_message(
            channel_id=channel_id,
            message=message,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            offline=offline,
            json_output=json_output,
        )


def _send_single_message(
    *,
    channel_id: str,
    message: str,
    nid_aut: str,
    nid_ses: str,
    offline: bool,
    json_output: bool,
) -> None:
    """Send a single message and exit."""
    try:
        with UnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
            chat = client.create_chat_client()

            try:
                chat.connect(channel_id, allow_offline=offline)
            except ChatNotLiveError:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "error": "Channel is not live",
                                "hint": "Use --offline to connect anyway",
                            }
                        )
                    )
                else:
                    console.print(
                        "[red]Error:[/red] Channel is not live.\n"
                        "Use [cyan]--offline[/cyan] to connect anyway."
                    )
                raise typer.Exit(1) from None
            except ChatConnectionError as e:
                if json_output:
                    console.print(json.dumps({"error": str(e)}))
                else:
                    console.print(f"[red]Connection error:[/red] {e}")
                raise typer.Exit(1) from None

            chat.send_message(message)

            if json_output:
                console.print(json.dumps({"status": "success", "message": "Message sent"}))
            else:
                console.print("[green]Message sent![/green]")

            chat.disconnect()

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        if json_output:
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


def _run_interactive_chat(
    *,
    channel_id: str,
    nid_aut: str,
    nid_ses: str,
    offline: bool,
    json_output: bool,
) -> None:
    """Run interactive chat mode."""

    async def run_chat() -> None:
        async with AsyncUnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
            chat = client.create_chat_client()

            @chat.on_chat
            async def handle_chat(msg: ChatMessage) -> None:
                console.print(format_chat_message(msg, json_output))

            @chat.on_donation
            async def handle_donation(msg: DonationMessage) -> None:
                console.print(format_donation_message(msg, json_output))

            # Get live detail first to check status
            try:
                live_detail = await client.live.get_live_detail(channel_id)
            except Exception as e:
                logger.error(f"Failed to get live detail: {e}")
                if json_output:
                    console.print(json.dumps({"error": str(e)}))
                else:
                    console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from None

            # Connect to chat
            try:
                if not json_output:
                    status_text = StatusText.LIVE if live_detail.is_live else StatusText.OFFLINE
                    console.print(
                        f"[green]Connecting to chat...[/green] "
                        f"({live_detail.channel_name or channel_id} - {status_text})"
                    )

                await chat.connect(channel_id, allow_offline=offline)

                if not json_output:
                    console.print(
                        f"[green]Connected![/green] Interactive chat for "
                        f"[cyan]{live_detail.channel_name or channel_id}[/cyan]"
                    )
                    console.print(
                        "[dim]Type messages and press Enter to send. Ctrl+C to exit.[/dim]\n"
                    )

            except ChatNotLiveError:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "error": "Channel is not live",
                                "channel_id": channel_id,
                                "hint": "Use --offline to connect anyway",
                            }
                        )
                    )
                else:
                    console.print(
                        f"[yellow]Channel {channel_id} is not live.[/yellow]\n"
                        f"Use [cyan]--offline[/cyan] to connect to chat anyway."
                    )
                raise typer.Exit(1) from None

            except ChatConnectionError as e:
                logger.error(f"Failed to connect to chat: {e}")
                if json_output:
                    console.print(json.dumps({"error": str(e)}))
                else:
                    console.print(f"[red]Connection error:[/red] {e}")
                raise typer.Exit(1) from None

            # Handle graceful shutdown
            loop = asyncio.get_running_loop()
            stop_event = asyncio.Event()

            def signal_handler() -> None:
                stop_event.set()
                chat.stop()

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)

            # Input loop for sending messages
            async def input_loop() -> None:
                while not stop_event.is_set():
                    try:
                        line = await asyncio.to_thread(input)
                        if line and not stop_event.is_set():
                            await chat.send_message(line)
                            console.print(format_sent_message(line, json_output))
                    except EOFError:
                        # stdin closed
                        break
                    except Exception:
                        # Input interrupted (likely by signal)
                        break

            input_task = asyncio.create_task(input_loop())

            try:
                await chat.run_forever()
            except asyncio.CancelledError:
                pass
            finally:
                input_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await input_task
                if not json_output:
                    console.print("\n[yellow]Disconnected[/yellow]")

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_chat())
