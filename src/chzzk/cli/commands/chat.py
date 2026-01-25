"""Chat commands for CLI."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import signal
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console

from chzzk.cli.formatter import ChatFormatter, FormatConfig
from chzzk.cli.logging import setup_logging
from chzzk.cli.tui import can_run_tui, run_tui
from chzzk.cli.tui.apps import ChatViewerApp, InteractiveChatApp
from chzzk.cli.writers import ChatWriter, OutputFormat, create_writer
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


def get_format_config(ctx: typer.Context) -> FormatConfig:
    """Get FormatConfig from context."""
    return FormatConfig.from_env_and_cli(
        cli_chat_format=ctx.obj.get("chat_format"),
        cli_donation_format=ctx.obj.get("donation_format"),
        cli_sent_format=ctx.obj.get("sent_format"),
        cli_time_format=ctx.obj.get("time_format"),
    )


def format_chat_message_json(msg: ChatMessage) -> str:
    """Format a chat message as JSON."""
    return json.dumps(
        {
            "type": "chat",
            "timestamp": datetime.now().isoformat(),
            "user_id_hash": msg.user_id_hash,
            "nickname": msg.nickname,
            "content": msg.content,
            "badge": (msg.profile.badge.get("name") if msg.profile and msg.profile.badge else None),
        }
    )


def format_donation_message_json(msg: DonationMessage) -> str:
    """Format a donation message as JSON."""
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


def format_sent_message_json(content: str) -> str:
    """Format a sent message as JSON."""
    return json.dumps(
        {
            "type": "sent",
            "timestamp": datetime.now().isoformat(),
            "content": content,
        }
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
    no_tui: Annotated[
        bool,
        typer.Option(
            "--no-tui",
            help="Disable TUI and use simple console output",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Save chat messages to file",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            help="Output format: jsonl, txt (default: jsonl)",
        ),
    ] = "jsonl",
) -> None:
    """Watch real-time chat messages from a channel.

    By default, only connects when the channel is live.
    Use --offline to connect to chat even when offline.

    By default, displays a full-screen TUI with scrollable messages.
    Use --no-tui for simple console output.

    Use --output to save messages to a file while watching.
    """
    nid_aut, nid_ses = get_auth_cookies(ctx)
    json_output = ctx.obj.get("json_output", False)
    config = get_config(ctx)
    format_config = get_format_config(ctx)

    # Create writer if output path specified
    writer: ChatWriter | None = None
    if output:
        try:
            writer = create_writer(output, OutputFormat(output_format))
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None
        except OSError as e:
            console.print(f"[red]Error:[/red] Cannot write to {output}: {e}")
            raise typer.Exit(1) from None

    try:
        # Use TUI if available and not disabled/json mode
        if not json_output and not no_tui and can_run_tui():
            # Reconfigure logging for TUI mode: disable console output to prevent
            # logs from corrupting the TUI display, keep file logging if configured
            setup_logging(
                ctx.obj.get("log_level", "WARNING"),
                log_file=ctx.obj.get("log_file"),
                disable_console=True,
            )

            viewer_app = ChatViewerApp(
                config=config,
                channel_id=channel_id,
                nid_aut=nid_aut,
                nid_ses=nid_ses,
                allow_offline=offline,
                writer=writer,
                format_config=format_config,
            )
            run_tui(viewer_app)

            if viewer_app.error_message:
                console.print(f"[red]Error:[/red] {viewer_app.error_message}")
                raise typer.Exit(1)
            return

        # Fallback to console output
        if not no_tui and not json_output:
            logger.info("TUI mode unavailable, using console mode")
        _run_watch_console(
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            offline=offline,
            json_output=json_output,
            writer=writer,
            format_config=format_config,
        )
    finally:
        if writer:
            writer.close()


def _run_watch_console(
    *,
    channel_id: str,
    nid_aut: str | None,
    nid_ses: str | None,
    offline: bool,
    json_output: bool,
    writer: ChatWriter | None = None,
    format_config: FormatConfig | None = None,
) -> None:
    """Run chat watch with console output (fallback mode)."""
    formatter = ChatFormatter(format_config)

    async def run_chat() -> None:
        async with AsyncUnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
            chat = client.create_chat_client()

            @chat.on_chat
            async def handle_chat(msg: ChatMessage) -> None:
                if json_output:
                    console.print(format_chat_message_json(msg))
                else:
                    console.print(formatter.format_chat(msg))
                if writer:
                    writer.write_chat(msg)

            @chat.on_donation
            async def handle_donation(msg: DonationMessage) -> None:
                if json_output:
                    console.print(format_donation_message_json(msg))
                else:
                    console.print(formatter.format_donation(msg))
                if writer:
                    writer.write_donation(msg)

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
    no_tui: Annotated[
        bool,
        typer.Option(
            "--no-tui",
            help="Disable TUI and use simple console input/output",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Save chat messages to file (interactive mode only)",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            help="Output format: jsonl, txt (default: jsonl)",
        ),
    ] = "jsonl",
) -> None:
    """Send a chat message to a channel.

    Requires authentication (NID_AUT and NID_SES cookies).

    By default, sends a single message and exits. Use --interactive for
    a persistent connection where you can send and receive messages.
    Use --offline to connect even when the channel is offline.

    In interactive mode, displays a full-screen TUI by default.
    Use --no-tui for simple console input/output.

    Use --output to save messages to a file (interactive mode only).
    """
    nid_aut, nid_ses = get_auth_cookies(ctx)
    json_output = ctx.obj.get("json_output", False)
    config = get_config(ctx)
    format_config = get_format_config(ctx)

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

    # Warn if output is specified in non-interactive mode
    if output and not interactive:
        if not json_output:
            console.print("[yellow]Warning:[/yellow] --output is ignored in non-interactive mode.")
        output = None

    # Create writer if output path specified (interactive mode only)
    writer: ChatWriter | None = None
    if output:
        try:
            writer = create_writer(output, OutputFormat(output_format))
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None
        except OSError as e:
            console.print(f"[red]Error:[/red] Cannot write to {output}: {e}")
            raise typer.Exit(1) from None

    try:
        if interactive:
            # Use TUI if available and not disabled/json mode
            if not json_output and not no_tui and can_run_tui():
                # Reconfigure logging for TUI mode: disable console output to prevent
                # logs from corrupting the TUI display, keep file logging if configured
                setup_logging(
                    ctx.obj.get("log_level", "WARNING"),
                    log_file=ctx.obj.get("log_file"),
                    disable_console=True,
                )

                interactive_app = InteractiveChatApp(
                    config=config,
                    channel_id=channel_id,
                    nid_aut=nid_aut,
                    nid_ses=nid_ses,
                    allow_offline=offline,
                    writer=writer,
                    format_config=format_config,
                )
                run_tui(interactive_app)

                if interactive_app.error_message:
                    console.print(f"[red]Error:[/red] {interactive_app.error_message}")
                    raise typer.Exit(1)
                return

            # Fallback to console interactive mode
            if not no_tui and not json_output:
                logger.info("TUI mode unavailable, using console mode")
            _run_interactive_chat_console(
                ctx=ctx,
                config=config,
                channel_id=channel_id,
                nid_aut=nid_aut,
                nid_ses=nid_ses,
                offline=offline,
                json_output=json_output,
                writer=writer,
                format_config=format_config,
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
    finally:
        if writer:
            writer.close()


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


def _run_interactive_chat_console(
    *,
    ctx: typer.Context,
    config: ConfigManager,
    channel_id: str,
    nid_aut: str,
    nid_ses: str,
    offline: bool,
    json_output: bool,
    writer: ChatWriter | None = None,
    format_config: FormatConfig | None = None,
) -> None:
    """Run interactive chat with console input/output (fallback mode).

    For non-JSON mode, uses Textual inline mode for proper cancellation.
    For JSON mode, uses async stdin reading with timeout on cancellation.
    """
    if not json_output:
        # Reconfigure logging for inline TUI mode: disable console output to prevent
        # logs from corrupting the TUI display, keep file logging if configured
        setup_logging(
            ctx.obj.get("log_level", "WARNING"),
            log_file=ctx.obj.get("log_file"),
            disable_console=True,
        )

        # Use inline Textual app for non-JSON mode - this allows proper cancellation
        interactive_app = InteractiveChatApp(
            config=config,
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            allow_offline=offline,
            inline_mode=True,
            writer=writer,
            format_config=format_config,
        )
        run_tui(interactive_app, inline=True, inline_height=15)

        if interactive_app.error_message:
            console.print(f"[red]Error:[/red] {interactive_app.error_message}")
            raise typer.Exit(1)
        return

    # JSON mode uses async stdin reading
    _run_interactive_chat_json(
        channel_id=channel_id,
        nid_aut=nid_aut,
        nid_ses=nid_ses,
        offline=offline,
        writer=writer,
    )


def _run_interactive_chat_json(
    *,
    channel_id: str,
    nid_aut: str,
    nid_ses: str,
    offline: bool,
    writer: ChatWriter | None = None,
) -> None:
    """Run interactive chat with JSON output (no TUI).

    Uses asyncio.to_thread(input) with timeout on cancellation.
    """

    async def run_chat() -> None:
        async with AsyncUnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses) as client:
            chat = client.create_chat_client()

            @chat.on_chat
            async def handle_chat(msg: ChatMessage) -> None:
                console.print(format_chat_message_json(msg))
                if writer:
                    writer.write_chat(msg)

            @chat.on_donation
            async def handle_donation(msg: DonationMessage) -> None:
                console.print(format_donation_message_json(msg))
                if writer:
                    writer.write_donation(msg)

            # Get live detail first to check status (validates channel exists)
            try:
                await client.live.get_live_detail(channel_id)
            except Exception as e:
                logger.error(f"Failed to get live detail: {e}")
                console.print(json.dumps({"error": str(e)}))
                raise typer.Exit(1) from None

            # Connect to chat
            try:
                await chat.connect(channel_id, allow_offline=offline)
            except ChatNotLiveError:
                console.print(
                    json.dumps(
                        {
                            "error": "Channel is not live",
                            "channel_id": channel_id,
                            "hint": "Use --offline to connect anyway",
                        }
                    )
                )
                raise typer.Exit(1) from None
            except ChatConnectionError as e:
                logger.error(f"Failed to connect to chat: {e}")
                console.print(json.dumps({"error": str(e)}))
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
                            console.print(format_sent_message_json(line))
                            if writer:
                                writer.write_sent(line)
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
                # Use timeout to avoid blocking on the uncancellable input() thread
                with contextlib.suppress(asyncio.CancelledError, TimeoutError):
                    await asyncio.wait_for(input_task, timeout=0.1)

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_chat())
