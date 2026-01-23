"""Authentication commands for CLI."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from chzzk.cli.tui import can_run_tui, run_tui
from chzzk.cli.tui.apps import LoginApp

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()


def get_config(ctx: typer.Context) -> ConfigManager:
    """Get ConfigManager from context."""
    return ctx.obj["config"]


def _prompt_login_fallback(config: ConfigManager) -> tuple[str, str]:
    """Fallback prompt-based login for non-TTY environments.

    Args:
        config: Configuration manager.

    Returns:
        Tuple of (nid_aut, nid_ses) values.
    """
    nid_aut = typer.prompt("NID_AUT cookie value")
    nid_ses = typer.prompt("NID_SES cookie value")
    return nid_aut, nid_ses


@app.command()
def login(
    ctx: typer.Context,
    nid_aut: Annotated[
        str | None,
        typer.Option(
            "--nid-aut",
            help="NID_AUT cookie value from Naver login",
        ),
    ] = None,
    nid_ses: Annotated[
        str | None,
        typer.Option(
            "--nid-ses",
            help="NID_SES cookie value from Naver login",
        ),
    ] = None,
    no_tui: Annotated[
        bool,
        typer.Option(
            "--no-tui",
            help="Disable TUI and use simple prompts",
        ),
    ] = False,
) -> None:
    """Save Naver authentication cookies.

    You can get these cookies from your browser after logging into Naver:
    1. Open browser DevTools (F12)
    2. Go to Application > Cookies > naver.com
    3. Find NID_AUT and NID_SES values

    By default, opens an interactive TUI for entering cookies.
    Use --no-tui to use simple prompts instead.
    """
    config = get_config(ctx)
    json_output = ctx.obj.get("json_output", False)

    # If both values provided via CLI, skip TUI/prompts
    if nid_aut and nid_ses:
        config.save_cookies(nid_aut, nid_ses)
        if json_output:
            console.print(json.dumps({"status": "success", "message": "Cookies saved"}))
        else:
            console.print(
                Panel(
                    f"Cookies saved to [cyan]{config.config_dir}[/cyan]",
                    title="[green]Login successful[/green]",
                    border_style="green",
                )
            )
        return

    # Try TUI if available and not disabled
    if not json_output and not no_tui and can_run_tui():
        login_app = LoginApp(config=config, nid_aut=nid_aut, nid_ses=nid_ses)
        run_tui(login_app)

        if login_app.result.cancelled:
            console.print("[yellow]Login cancelled[/yellow]")
            raise typer.Exit(0)

        if login_app.result.success:
            if json_output:
                console.print(json.dumps({"status": "success", "message": "Cookies saved"}))
            else:
                console.print(
                    Panel(
                        f"Cookies saved to [cyan]{config.config_dir}[/cyan]",
                        title="[green]Login successful[/green]",
                        border_style="green",
                    )
                )
        else:
            console.print("[red]Login failed[/red]")
            raise typer.Exit(1)
        return

    # Fallback to simple prompts
    try:
        final_nid_aut, final_nid_ses = _prompt_login_fallback(config)
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Login cancelled[/yellow]")
        raise typer.Exit(0) from None

    config.save_cookies(final_nid_aut, final_nid_ses)

    if json_output:
        console.print(json.dumps({"status": "success", "message": "Cookies saved"}))
    else:
        console.print(
            Panel(
                f"Cookies saved to [cyan]{config.config_dir}[/cyan]",
                title="[green]Login successful[/green]",
                border_style="green",
            )
        )


@app.command()
def status(ctx: typer.Context) -> None:
    """Check authentication status."""
    config = get_config(ctx)
    nid_aut, nid_ses = config.get_auth_cookies(
        cli_nid_aut=ctx.obj.get("nid_aut"),
        cli_nid_ses=ctx.obj.get("nid_ses"),
    )

    has_auth = bool(nid_aut and nid_ses)

    if ctx.obj.get("json_output"):
        result = {
            "authenticated": has_auth,
            "has_nid_aut": bool(nid_aut),
            "has_nid_ses": bool(nid_ses),
            "has_stored_cookies": config.has_stored_cookies(),
        }
        console.print(json.dumps(result))
    else:
        if has_auth:
            # Mask cookie values for display
            aut_masked = nid_aut[:8] + "..." if nid_aut and len(nid_aut) > 8 else nid_aut
            ses_masked = nid_ses[:8] + "..." if nid_ses and len(nid_ses) > 8 else nid_ses

            console.print(
                Panel(
                    f"[green]Authenticated[/green]\n\n"
                    f"NID_AUT: [dim]{aut_masked}[/dim]\n"
                    f"NID_SES: [dim]{ses_masked}[/dim]\n\n"
                    f"Stored cookies: {'Yes' if config.has_stored_cookies() else 'No'}",
                    title="Authentication Status",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "[red]Not authenticated[/red]\n\n"
                    "Run [cyan]chzzk auth login[/cyan] to save your cookies.",
                    title="Authentication Status",
                    border_style="red",
                )
            )


@app.command()
def logout(ctx: typer.Context) -> None:
    """Delete stored authentication cookies."""
    config = get_config(ctx)

    if not config.has_stored_cookies():
        if ctx.obj.get("json_output"):
            console.print(json.dumps({"status": "info", "message": "No cookies stored"}))
        else:
            console.print("[yellow]No stored cookies to delete.[/yellow]")
        return

    config.delete_cookies()

    if ctx.obj.get("json_output"):
        console.print(json.dumps({"status": "success", "message": "Cookies deleted"}))
    else:
        console.print(
            Panel(
                "Stored cookies have been deleted.",
                title="[green]Logout successful[/green]",
                border_style="green",
            )
        )
