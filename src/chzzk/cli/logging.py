"""Logging configuration for CLI."""

from __future__ import annotations

import logging


def setup_logging(level: str = "WARNING") -> None:
    """Set up CLI logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
    """
    log_level = getattr(logging, level.upper(), logging.WARNING)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set chzzk loggers
    chzzk_logger = logging.getLogger("chzzk")
    chzzk_logger.setLevel(log_level)
