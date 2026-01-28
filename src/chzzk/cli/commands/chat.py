"""Chat commands for CLI."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import signal
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console

from chzzk.cli.formatter import ChatFormatter, FormatConfig
from chzzk.cli.writers import ChatWriter, OutputFormat, create_writer, generate_chat_log_filename
from chzzk.constants import StatusText
from chzzk.exceptions import ChatConnectionError, ChatNotLiveError
from chzzk.unofficial import (
    AsyncUnofficialChzzkClient,
    ChatMessage,
    DonationMessage,
    UnofficialChzzkClient,
)
from chzzk.unofficial.models.reconnect import ReconnectEvent, ReconnectReason, StatusChangeEvent

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = logging.getLogger("chzzk.cli.chat")


def get_auth_cookies(ctx: typer.Context) -> tuple[str | None, str | None]:
    """Get authentication cookies from context."""
    config = ctx.obj["config"]
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
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            envvar="CHZZK_CHAT_OUTPUT",
            help="Save chat messages to file",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            envvar="CHZZK_CHAT_OUTPUT_FORMAT",
            help="Output format: jsonl, txt (default: jsonl)",
        ),
    ] = "jsonl",
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-d",
            envvar="CHZZK_CHAT_OUTPUT_DIR",
            help="Directory to save chat logs (auto-generates filename based on stream info)",
        ),
    ] = None,
) -> None:
    """Watch real-time chat messages from a channel.

    By default, only connects when the channel is live.
    Use --offline to connect to chat even when offline.

    Use --output to save messages to a file while watching.
    Use --output-dir to auto-generate filename based on stream info.
    """
    nid_aut, nid_ses = get_auth_cookies(ctx)
    json_output = ctx.obj.get("json_output", False)
    format_config = get_format_config(ctx)

    # Validate mutually exclusive options
    if output and output_dir:
        console.print(
            "[red]Error:[/red] --output and --output-dir are mutually exclusive. Use only one."
        )
        raise typer.Exit(1)

    # Create writer if output path specified (output_dir is handled inside _run_watch_console)
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
        _run_watch_console(
            channel_id=channel_id,
            nid_aut=nid_aut,
            nid_ses=nid_ses,
            offline=offline,
            json_output=json_output,
            writer=writer,
            format_config=format_config,
            output_dir=output_dir,
            output_format=OutputFormat(output_format),
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
    output_dir: Path | None = None,
    output_format: OutputFormat = OutputFormat.JSONL,
) -> None:
    """Run chat watch with console output (fallback mode)."""
    formatter = ChatFormatter(format_config)
    # Track writer created from output_dir (needs to be closed on exit)
    output_dir_writer: ChatWriter | None = None

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

            @chat.on_live
            async def handle_live(event: StatusChangeEvent) -> None:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "event": "live",
                                "live_id": event.live_id,
                                "title": event.live_title,
                            }
                        )
                    )
                else:
                    title = event.live_title or "제목 없음"
                    console.print(f"\n[green]방송이 시작되었습니다![/green] {title}")

            @chat.on_offline
            async def handle_offline(event: StatusChangeEvent) -> None:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "event": "offline",
                                "live_id": event.live_id,
                                "title": event.live_title,
                            }
                        )
                    )
                else:
                    console.print(
                        "\n[yellow]방송이 종료되었습니다.[/yellow] "
                        "재시작을 기다리는 중... (Ctrl+C로 종료)"
                    )

            @chat.on_reconnect
            async def handle_reconnect(event: ReconnectEvent) -> None:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "event": "reconnect",
                                "reason": event.reason.value,
                                "old_chat_channel_id": event.old_chat_channel_id,
                                "new_chat_channel_id": event.new_chat_channel_id,
                            }
                        )
                    )
                else:
                    if event.reason == ReconnectReason.STREAM_RESTARTED:
                        console.print("[green]채팅에 다시 연결되었습니다.[/green]\n")
                    else:
                        console.print(
                            "[yellow]채팅 채널이 변경되어 다시 연결되었습니다.[/yellow]\n"
                        )

            @chat.on_reconnect_error
            async def handle_reconnect_error(error: Exception) -> None:
                if json_output:
                    console.print(json.dumps({"event": "reconnect_error", "error": str(error)}))
                else:
                    console.print(f"[red]재연결 실패:[/red] {error}")

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

            # Create writer from output_dir if specified (after getting live_detail)
            nonlocal writer, output_dir_writer
            if output_dir and not writer:
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = generate_chat_log_filename(
                        output_dir=output_dir,
                        channel_id=channel_id,
                        live_id=live_detail.live_id,
                        open_date=live_detail.open_date,
                        format=output_format,
                    )
                    output_dir_writer = create_writer(output_path, output_format)
                    writer = output_dir_writer
                    if not json_output:
                        console.print(f"[dim]Saving chat to: {output_path}[/dim]")
                except OSError as e:
                    console.print(f"[red]Error:[/red] Cannot write to {output_dir}: {e}")
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

    try:
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(run_chat())
    finally:
        if output_dir_writer:
            output_dir_writer.close()


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
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            envvar="CHZZK_CHAT_OUTPUT",
            help="Save chat messages to file (interactive mode only)",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            envvar="CHZZK_CHAT_OUTPUT_FORMAT",
            help="Output format: jsonl, txt (default: jsonl)",
        ),
    ] = "jsonl",
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-d",
            envvar="CHZZK_CHAT_OUTPUT_DIR",
            help="Directory to save chat logs (interactive mode only, auto-generates filename)",
        ),
    ] = None,
) -> None:
    """Send a chat message to a channel.

    Requires authentication (NID_AUT and NID_SES cookies).

    By default, sends a single message and exits. Use --interactive for
    a persistent connection where you can send and receive messages.
    Use --offline to connect even when the channel is offline.

    Use --output to save messages to a file (interactive mode only).
    Use --output-dir to auto-generate filename based on stream info (interactive mode only).
    """
    nid_aut, nid_ses = get_auth_cookies(ctx)
    json_output = ctx.obj.get("json_output", False)
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

    # Validate mutually exclusive options
    if output and output_dir:
        console.print(
            "[red]Error:[/red] --output and --output-dir are mutually exclusive. Use only one."
        )
        raise typer.Exit(1)

    # Warn if output/output_dir is specified in non-interactive mode
    if output and not interactive:
        if not json_output:
            console.print("[yellow]Warning:[/yellow] --output is ignored in non-interactive mode.")
        output = None
    if output_dir and not interactive:
        if not json_output:
            console.print(
                "[yellow]Warning:[/yellow] --output-dir is ignored in non-interactive mode."
            )
        output_dir = None

    # Create writer if output path specified (interactive mode only)
    # output_dir is handled inside _run_interactive_chat_console
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
            _run_interactive_chat_console(
                channel_id=channel_id,
                nid_aut=nid_aut,
                nid_ses=nid_ses,
                offline=offline,
                json_output=json_output,
                writer=writer,
                format_config=format_config,
                output_dir=output_dir,
                output_format=OutputFormat(output_format),
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
    channel_id: str,
    nid_aut: str,
    nid_ses: str,
    offline: bool,
    json_output: bool,
    writer: ChatWriter | None = None,
    format_config: FormatConfig | None = None,
    output_dir: Path | None = None,
    output_format: OutputFormat = OutputFormat.JSONL,
) -> None:
    """Run interactive chat with console input/output.

    Uses async stdin reading with chat message display.
    """
    formatter = ChatFormatter(format_config)
    # Track writer created from output_dir (needs to be closed on exit)
    output_dir_writer: ChatWriter | None = None

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

            @chat.on_live
            async def handle_live(event: StatusChangeEvent) -> None:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "event": "live",
                                "live_id": event.live_id,
                                "title": event.live_title,
                            }
                        )
                    )
                else:
                    title = event.live_title or "제목 없음"
                    console.print(f"\n[green]방송이 시작되었습니다![/green] {title}")

            @chat.on_offline
            async def handle_offline(event: StatusChangeEvent) -> None:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "event": "offline",
                                "live_id": event.live_id,
                                "title": event.live_title,
                            }
                        )
                    )
                else:
                    console.print(
                        "\n[yellow]방송이 종료되었습니다.[/yellow] "
                        "재시작을 기다리는 중... (Ctrl+C로 종료)"
                    )

            @chat.on_reconnect
            async def handle_reconnect(event: ReconnectEvent) -> None:
                if json_output:
                    console.print(
                        json.dumps(
                            {
                                "event": "reconnect",
                                "reason": event.reason.value,
                                "old_chat_channel_id": event.old_chat_channel_id,
                                "new_chat_channel_id": event.new_chat_channel_id,
                            }
                        )
                    )
                else:
                    if event.reason == ReconnectReason.STREAM_RESTARTED:
                        console.print("[green]채팅에 다시 연결되었습니다.[/green]\n")
                    else:
                        console.print(
                            "[yellow]채팅 채널이 변경되어 다시 연결되었습니다.[/yellow]\n"
                        )

            @chat.on_reconnect_error
            async def handle_reconnect_error(error: Exception) -> None:
                if json_output:
                    console.print(json.dumps({"event": "reconnect_error", "error": str(error)}))
                else:
                    console.print(f"[red]재연결 실패:[/red] {error}")

            # Get live detail first to check status (validates channel exists)
            try:
                live_detail = await client.live.get_live_detail(channel_id)
            except Exception as e:
                logger.error(f"Failed to get live detail: {e}")
                if json_output:
                    console.print(json.dumps({"error": str(e)}))
                else:
                    console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from None

            # Create writer from output_dir if specified (after getting live_detail)
            nonlocal writer, output_dir_writer
            if output_dir and not writer:
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = generate_chat_log_filename(
                        output_dir=output_dir,
                        channel_id=channel_id,
                        live_id=live_detail.live_id,
                        open_date=live_detail.open_date,
                        format=output_format,
                    )
                    output_dir_writer = create_writer(output_path, output_format)
                    writer = output_dir_writer
                    if not json_output:
                        console.print(f"[dim]Saving chat to: {output_path}[/dim]")
                except OSError as e:
                    console.print(f"[red]Error:[/red] Cannot write to {output_dir}: {e}")
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
                session: PromptSession[str] = PromptSession()
                while not stop_event.is_set():
                    try:
                        with patch_stdout(raw=True):
                            line = await session.prompt_async("")
                        if line and not stop_event.is_set():
                            await chat.send_message(line)
                            if json_output:
                                console.print(format_sent_message_json(line))
                            else:
                                console.print(formatter.format_sent(line))
                            if writer:
                                writer.write_sent(line)
                    except (EOFError, KeyboardInterrupt):
                        # prompt_toolkit catches SIGINT and raises KeyboardInterrupt
                        # We need to trigger shutdown here as well
                        stop_event.set()
                        chat.stop()
                        break
                    except asyncio.CancelledError:
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

    try:
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(run_chat())
    finally:
        if output_dir_writer:
            output_dir_writer.close()
