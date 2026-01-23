"""Logging configuration for Chzzk SDK."""

from __future__ import annotations

import logging


def configure_logging(level: str | int = "WARNING") -> None:
    """Configure logging for the Chzzk SDK.

    Args:
        level: Logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
               Can be a string name or logging level constant.

    Example:
        >>> from chzzk.logging import configure_logging
        >>> configure_logging("DEBUG")  # Enable debug output
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.WARNING)

    logging.getLogger("chzzk").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a Chzzk module.

    Args:
        name: The module name (typically __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
