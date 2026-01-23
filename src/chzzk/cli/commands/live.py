"""Live stream commands for CLI."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from chzzk.unofficial import LiveStatus, UnofficialChzzkClient

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = logging.getLogger("chzzk.cli.live")


def get_config(ctx: typer.Context) -> ConfigManager:
    """Get ConfigManager from context."""
    return ctx.obj["config"]


def get_client(ctx: typer.Context) -> UnofficialChzzkClient:
    """Create an unofficial client from context."""
    config = get_config(ctx)
    nid_aut, nid_ses = config.get_auth_cookies(
        cli_nid_aut=ctx.obj.get("nid_aut"),
        cli_nid_ses=ctx.obj.get("nid_ses"),
    )
    return UnofficialChzzkClient(nid_aut=nid_aut, nid_ses=nid_ses)


@app.command()
def info(
    ctx: typer.Context,
    channel_id: Annotated[
        str,
        typer.Argument(help="Channel ID to get live info for"),
    ],
) -> None:
    """Get detailed live stream information for a channel."""
    try:
        with get_client(ctx) as client:
            live_detail = client.live.get_live_detail(channel_id)
    except Exception as e:
        logger.error(f"Failed to get live info: {e}")
        if ctx.obj.get("json_output"):
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if ctx.obj.get("json_output"):
        console.print(live_detail.model_dump_json(by_alias=True, indent=2))
    else:
        status_color = "green" if live_detail.is_live else "red"
        status_text = "LIVE" if live_detail.is_live else "OFFLINE"

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Channel", live_detail.channel_name or "-")
        table.add_row("Status", f"[{status_color}]{status_text}[/{status_color}]")
        table.add_row("Title", live_detail.live_title or "-")
        table.add_row("Category", live_detail.live_category_value or "-")
        table.add_row("Viewers", str(live_detail.concurrent_user_count))
        table.add_row("Total Views", str(live_detail.accumulated_user_count))
        table.add_row("Chat Channel ID", live_detail.chat_channel_id or "-")

        if live_detail.open_date:
            table.add_row("Started At", live_detail.open_date)

        console.print(Panel(table, title=f"Live Info: {channel_id}", border_style="blue"))


@app.command()
def status(
    ctx: typer.Context,
    channel_id: Annotated[
        str,
        typer.Argument(help="Channel ID to check status for"),
    ],
) -> None:
    """Get simple live status (LIVE or OFFLINE) for a channel."""
    try:
        with get_client(ctx) as client:
            live_detail = client.live.get_live_detail(channel_id)
    except Exception as e:
        logger.error(f"Failed to get live status: {e}")
        if ctx.obj.get("json_output"):
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    status_value = LiveStatus.OPEN if live_detail.is_live else LiveStatus.CLOSE

    if ctx.obj.get("json_output"):
        result = {
            "channel_id": channel_id,
            "status": status_value.value,
            "is_live": live_detail.is_live,
        }
        console.print(json.dumps(result))
    else:
        if live_detail.is_live:
            console.print(f"[green]LIVE[/green] - {live_detail.channel_name or channel_id}")
        else:
            console.print(f"[red]OFFLINE[/red] - {live_detail.channel_name or channel_id}")
