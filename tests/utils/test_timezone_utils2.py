"""Unit tests for timezone utilities — duration and workflow tests."""

from datetime import datetime, timedelta, timezone

import pytest

from mcp_coder.utils.timezone_utils import (
    format_for_cache,
    is_within_duration,
    parse_iso_timestamp,
)


class TestIsWithinDuration:
    """Test duration checking."""

    def test_within_duration_true(self) -> None:
        """Test timestamp within duration returns True."""
        reference = datetime.now(timezone.utc)
        timestamp = reference - timedelta(seconds=30)

        result = is_within_duration(timestamp, 60.0, reference)
        assert result is True

    def test_within_duration_false(self) -> None:
        """Test timestamp outside duration returns False."""
        reference = datetime.now(timezone.utc)
        timestamp = reference - timedelta(seconds=90)

        result = is_within_duration(timestamp, 60.0, reference)
        assert result is False

    def test_within_duration_exact_boundary(self) -> None:
        """Test timestamp at exact boundary."""
        reference = datetime.now(timezone.utc)
        timestamp = reference - timedelta(seconds=60)

        result = is_within_duration(timestamp, 60.0, reference)
        assert result is True

    def test_within_duration_future_timestamp(self) -> None:
        """Test future timestamp within duration."""
        reference = datetime.now(timezone.utc)
        timestamp = reference + timedelta(seconds=30)

        result = is_within_duration(timestamp, 60.0, reference)
        assert result is True

    def test_within_duration_no_reference_time(self) -> None:
        """Test duration check against current time."""
        timestamp = datetime.now(timezone.utc) - timedelta(seconds=30)

        result = is_within_duration(timestamp, 60.0)
        assert result is True


class TestEndToEndWorkflow:
    """Test complete workflows combining multiple functions."""

    def test_parse_format_roundtrip(self) -> None:
        """Test parsing and formatting roundtrip."""
        original = "2026-01-03T23:36:14.620992+01:00"

        # Parse to UTC datetime
        parsed = parse_iso_timestamp(original)

        # Verify UTC conversion happened
        assert parsed == datetime(2026, 1, 3, 22, 36, 14, 620992, timezone.utc)

        # Format for cache
        cache_format = format_for_cache(parsed)
        assert cache_format == "2026-01-03T22:36:14.620992+00:00"

        # Parse back from cache format
        reparsed = parse_iso_timestamp(cache_format)
        assert reparsed == parsed

    def test_cache_timestamp_comparison(self) -> None:
        """Test realistic cache timestamp comparison scenario."""
        # Simulate cache timestamp (CET)
        cache_time_str = "2026-01-03T23:36:14.620992+01:00"
        cache_time = parse_iso_timestamp(cache_time_str)

        # Simulate user change time (CET midnight)
        user_change_str = "2026-01-04T00:00:00+01:00"
        user_change = parse_iso_timestamp(user_change_str)

        # Verify comparison (user change should be after cache time in UTC)
        assert user_change > cache_time

        # Verify the UTC times are correct
        # cache_time: 23:36 CET = 22:36 UTC
        # user_change: 00:00 CET = 23:00 UTC
        assert cache_time == datetime(2026, 1, 3, 22, 36, 14, 620992, timezone.utc)
        assert user_change == datetime(2026, 1, 3, 23, 0, 0, 0, timezone.utc)

        # Verify cache formatting works correctly
        cache_format = format_for_cache(cache_time)
        assert cache_format == "2026-01-03T22:36:14.620992+00:00"
