"""Main CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from chzzk.cli.commands import auth, chat, live
from chzzk.cli.config import ConfigManager
from chzzk.cli.logging import setup_logging

# Load environment variables from .env file
load_dotenv()

app = typer.Typer(
    name="chzzk",
    help="Unofficial CLI for Chzzk (NAVER Live Streaming Platform)",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(auth.app, name="auth", help="Authentication commands")
app.add_typer(live.app, name="live", help="Live stream commands")
app.add_typer(chat.app, name="chat", help="Chat commands")


@app.callback()
def main(
    ctx: typer.Context,
    nid_aut: Annotated[
        str | None,
        typer.Option(
            "--nid-aut",
            envvar="CHZZK_NID_AUT",
            help="NID_AUT cookie value for authentication",
        ),
    ] = None,
    nid_ses: Annotated[
        str | None,
        typer.Option(
            "--nid-ses",
            envvar="CHZZK_NID_SES",
            help="NID_SES cookie value for authentication",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output in JSON format",
        ),
    ] = False,
    log_level: Annotated[
        str | None,
        typer.Option(
            "--log-level",
            envvar="CHZZK_LOG_LEVEL",
            help="Log level (DEBUG, INFO, WARNING, ERROR)",
        ),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(
            "--log-file",
            envvar="CHZZK_LOG_FILE",
            help="Save application logs to file",
        ),
    ] = None,
    no_console_log: Annotated[
        bool,
        typer.Option(
            "--no-console-log",
            envvar="CHZZK_NO_CONSOLE_LOG",
            help="Disable console (stderr) logging output",
        ),
    ] = False,
) -> None:
    """Chzzk CLI - Unofficial CLI for Chzzk streaming platform."""
    ctx.ensure_object(dict)

    config = ConfigManager()

    # Set up logging
    effective_log_level = config.get_log_level(log_level)
    setup_logging(effective_log_level, log_file=log_file, disable_console=no_console_log)

    # Store global options in context
    ctx.obj["config"] = config
    ctx.obj["nid_aut"] = nid_aut
    ctx.obj["nid_ses"] = nid_ses
    ctx.obj["json_output"] = json_output
    ctx.obj["log_level"] = effective_log_level
    ctx.obj["log_file"] = log_file
    ctx.obj["no_console_log"] = no_console_log


if __name__ == "__main__":
    app()
