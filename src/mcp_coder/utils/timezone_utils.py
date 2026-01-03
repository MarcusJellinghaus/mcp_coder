"""Timezone utilities for consistent datetime handling across mcp-coder.

This module provides utilities for:
- Parsing ISO 8601 timestamps with timezone awareness
- Converting between timezones consistently
- Formatting timestamps for different APIs (GitHub, etc.)
- Handling timezone-naive and timezone-aware datetimes safely

All functions in this module ensure consistent UTC-based handling
to prevent timezone conversion bugs.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO 8601 timestamp string into timezone-aware datetime in UTC.

    Handles various ISO 8601 formats:
    - "2026-01-03T23:36:14.620992+01:00" (with timezone offset)
    - "2026-01-03T23:36:14Z" (UTC with Z suffix)
    - "2026-01-03T23:36:14" (naive, assumed UTC)
    - "2026-01-03T23:36:14.620992Z" (UTC with microseconds)

    Args:
        timestamp_str: ISO 8601 formatted timestamp string

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        ValueError: If timestamp format is invalid

    Example:
        >>> dt = parse_iso_timestamp("2026-01-03T23:36:14.620992+01:00")
        >>> print(dt)  # 2026-01-03 22:36:14.620992+00:00 (converted to UTC)
        >>> dt = parse_iso_timestamp("2026-01-03T23:36:14Z")
        >>> print(dt)  # 2026-01-03 23:36:14+00:00 (already UTC)
    """
    if not timestamp_str:
        raise ValueError("Timestamp string cannot be empty")

    try:
        # Handle Z suffix (UTC indicator)
        if timestamp_str.endswith("Z"):
            # Replace Z with explicit UTC offset for fromisoformat()
            timestamp_str = timestamp_str[:-1] + "+00:00"

        # Parse with fromisoformat (handles timezone offsets)
        parsed_dt = datetime.fromisoformat(timestamp_str)

        # If naive (no timezone), assume UTC
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if not already
            parsed_dt = parsed_dt.astimezone(timezone.utc)

        return parsed_dt

    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid ISO timestamp format '{timestamp_str}': {e}")


def now_utc() -> datetime:
    """Get current time as timezone-aware datetime in UTC.

    Returns:
        Current time in UTC timezone

    Example:
        >>> now = now_utc()
        >>> print(now.tzinfo)  # timezone.utc
    """
    return datetime.now(timezone.utc)


def format_for_github_api(dt: datetime) -> str:
    """Format datetime for GitHub API 'since' parameter.

    GitHub API expects ISO 8601 format ending with 'Z' (UTC).

    Args:
        dt: Timezone-aware datetime (will be converted to UTC if needed)

    Returns:
        ISO 8601 string ending with 'Z' for GitHub API

    Raises:
        ValueError: If datetime is timezone-naive

    Example:
        >>> dt = parse_iso_timestamp("2026-01-03T23:36:14.620992+01:00")
        >>> github_format = format_for_github_api(dt)
        >>> print(github_format)  # "2026-01-03T22:36:14.620992Z"
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")

    # Convert to UTC and format with Z suffix
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat().replace("+00:00", "Z")


def format_for_cache(dt: datetime) -> str:
    """Format datetime for cache storage with timezone info.

    Args:
        dt: Timezone-aware datetime

    Returns:
        ISO 8601 string with timezone offset

    Raises:
        ValueError: If datetime is timezone-naive

    Example:
        >>> dt = now_utc()
        >>> cache_format = format_for_cache(dt)
        >>> print(cache_format)  # "2026-01-03T23:36:14.620992+00:00"
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")

    return dt.isoformat()


def ensure_timezone_aware(dt: datetime, assume_utc: bool = True) -> datetime:
    """Ensure a datetime is timezone-aware.

    Args:
        dt: Datetime that may or may not have timezone info
        assume_utc: If True, treat naive datetimes as UTC. If False, use local timezone.

    Returns:
        Timezone-aware datetime

    Example:
        >>> naive_dt = datetime(2026, 1, 3, 23, 36, 14)
        >>> aware_dt = ensure_timezone_aware(naive_dt)
        >>> print(aware_dt.tzinfo)  # timezone.utc
    """
    if dt.tzinfo is None:
        if assume_utc:
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Use system local timezone
            return dt.astimezone()
    return dt


def calculate_elapsed_seconds(
    start_time: datetime, end_time: Optional[datetime] = None
) -> float:
    """Calculate elapsed seconds between two timezone-aware datetimes.

    Args:
        start_time: Start time (timezone-aware)
        end_time: End time (timezone-aware). If None, uses current UTC time.

    Returns:
        Elapsed seconds as float

    Raises:
        ValueError: If either datetime is timezone-naive

    Example:
        >>> start = parse_iso_timestamp("2026-01-03T23:36:14+01:00")
        >>> end = parse_iso_timestamp("2026-01-03T23:37:14+01:00")
        >>> elapsed = calculate_elapsed_seconds(start, end)
        >>> print(elapsed)  # 60.0
    """
    if start_time.tzinfo is None:
        raise ValueError("start_time must be timezone-aware")

    if end_time is None:
        end_time = now_utc()
    elif end_time.tzinfo is None:
        raise ValueError("end_time must be timezone-aware")

    return (end_time - start_time).total_seconds()


def is_within_duration(
    timestamp: datetime,
    duration_seconds: float,
    reference_time: Optional[datetime] = None,
) -> bool:
    """Check if a timestamp is within a duration from a reference time.

    Args:
        timestamp: The timestamp to check (timezone-aware)
        duration_seconds: Duration in seconds
        reference_time: Reference time (timezone-aware). If None, uses current UTC time.

    Returns:
        True if timestamp is within duration from reference_time

    Example:
        >>> ts = parse_iso_timestamp("2026-01-03T23:36:14Z")
        >>> # Check if timestamp is within last 60 seconds
        >>> within_minute = is_within_duration(ts, 60)
    """
    if reference_time is None:
        reference_time = now_utc()

    elapsed = calculate_elapsed_seconds(timestamp, reference_time)
    return abs(elapsed) <= duration_seconds
