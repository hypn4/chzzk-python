"""Logging configuration for CLI."""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(
    level: str = "WARNING",
    log_file: Path | None = None,
    disable_console: bool = False,
) -> None:
    """Set up CLI logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to log file for file-based logging.
        disable_console: If True, disable console (stderr) logging.
            Use this for TUI mode to prevent logs from corrupting the display.
    """
    log_level = getattr(logging, level.upper(), logging.WARNING)

    handlers: list[logging.Handler] = []

    # Add console handler only if not disabled (e.g., not in TUI mode)
    if not disable_console:
        handlers.append(logging.StreamHandler())

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        handlers.append(file_handler)

    # Add NullHandler if no handlers configured to prevent "no handler" warnings
    if not handlers:
        handlers.append(logging.NullHandler())

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )

    # Set chzzk loggers
    chzzk_logger = logging.getLogger("chzzk")
    chzzk_logger.setLevel(log_level)
