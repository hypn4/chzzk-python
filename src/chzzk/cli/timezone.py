"""Timezone utilities for CLI output.

This module provides centralized timezone handling for consistent timestamp
display across different environments (local, Docker, etc.).

The timezone can be configured via the CHZZK_TIMEZONE environment variable.
Default timezone is Asia/Seoul (KST).
"""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Seoul"


def get_timezone() -> ZoneInfo:
    """Get the configured timezone.

    Returns:
        ZoneInfo object for the configured timezone.
        Uses CHZZK_TIMEZONE environment variable if set,
        otherwise defaults to Asia/Seoul.
    """
    tz_name = os.environ.get("CHZZK_TIMEZONE", DEFAULT_TIMEZONE)
    return ZoneInfo(tz_name)


def now() -> datetime:
    """Get current datetime in the configured timezone.

    Returns:
        Current datetime with timezone info.
    """
    return datetime.now(get_timezone())


def from_timestamp(timestamp: float) -> datetime:
    """Convert Unix timestamp to datetime in the configured timezone.

    Args:
        timestamp: Unix timestamp (seconds since epoch).

    Returns:
        Datetime object in the configured timezone.
    """
    return datetime.fromtimestamp(timestamp, get_timezone())
