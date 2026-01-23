"""TUI utility functions."""

from __future__ import annotations

import logging
import shutil
import sys
from typing import TYPE_CHECKING, TypeVar

logger = logging.getLogger("chzzk.cli.tui")

if TYPE_CHECKING:
    from collections.abc import Callable

    from textual.app import App

T = TypeVar("T")


def can_run_tui(min_cols: int = 60, min_lines: int = 20) -> bool:
    """Check if the terminal supports TUI rendering.

    Verifies that:
    - stdout is a TTY (not piped/redirected)
    - Terminal size meets minimum requirements

    Args:
        min_cols: Minimum required terminal columns.
        min_lines: Minimum required terminal lines.

    Returns:
        True if TUI can be rendered, False otherwise.
    """
    if not sys.stdout.isatty():
        logger.debug("TUI disabled: not a TTY")
        return False

    size = shutil.get_terminal_size()
    if size.columns < min_cols or size.lines < min_lines:
        logger.debug(
            "TUI disabled: terminal size %dx%d < minimum %dx%d",
            size.columns,
            size.lines,
            min_cols,
            min_lines,
        )
        return False
    return True


def run_tui(
    app: App[T],
    *,
    inline: bool = False,
    inline_height: int | None = None,
    fallback_fn: Callable[[], T] | None = None,
) -> T | None:
    """Run a Textual TUI app with optional inline mode and fallback.

    Args:
        app: The Textual app to run.
        inline: If True, run in inline mode (preserves terminal output).
        inline_height: Height for inline mode (auto-detected if None).
        fallback_fn: Function to call if TTY is not available.

    Returns:
        The app's return value, or fallback result.

    Raises:
        RuntimeError: If no TTY and no fallback provided.
    """
    if not sys.stdout.isatty():
        if fallback_fn is not None:
            return fallback_fn()
        raise RuntimeError("TTY required for TUI mode")

    if inline:
        return app.run(inline=True, inline_no_clear=True)
    return app.run()
