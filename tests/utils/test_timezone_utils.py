"""Unit tests for timezone utilities."""

from datetime import datetime, timedelta, timezone

import pytest

from mcp_coder.utils.timezone_utils import (
    format_for_cache,
    now_utc,
    parse_iso_timestamp,
)


class TestParseIsoTimestamp:
    """Test ISO timestamp parsing with various formats."""

    def test_parse_with_timezone_offset(self) -> None:
        """Test parsing timestamp with timezone offset."""
        timestamp_str = "2026-01-03T23:36:14.620992+01:00"
        result = parse_iso_timestamp(timestamp_str)

        # Should be converted to UTC
        expected = datetime(2026, 1, 3, 22, 36, 14, 620992, timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc

    def test_parse_with_z_suffix(self) -> None:
        """Test parsing timestamp with Z suffix (UTC)."""
        timestamp_str = "2026-01-03T23:36:14.620992Z"
        result = parse_iso_timestamp(timestamp_str)

        expected = datetime(2026, 1, 3, 23, 36, 14, 620992, timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc

    def test_parse_z_suffix_without_microseconds(self) -> None:
        """Test parsing Z suffix without microseconds."""
        timestamp_str = "2026-01-03T23:36:14Z"
        result = parse_iso_timestamp(timestamp_str)

        expected = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        assert result == expected

    def test_parse_naive_timestamp(self) -> None:
        """Test parsing naive timestamp (assumes UTC)."""
        timestamp_str = "2026-01-03T23:36:14"
        result = parse_iso_timestamp(timestamp_str)

        expected = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc

    def test_parse_negative_offset(self) -> None:
        """Test parsing timestamp with negative timezone offset."""
        timestamp_str = "2026-01-03T23:36:14-05:00"  # EST
        result = parse_iso_timestamp(timestamp_str)

        # 23:36 EST = 04:36 UTC next day
        expected = datetime(2026, 1, 4, 4, 36, 14, 0, timezone.utc)
        assert result == expected

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string raises ValueError."""
        with pytest.raises(ValueError, match="Timestamp string cannot be empty"):
            parse_iso_timestamp("")

    def test_parse_invalid_format(self) -> None:
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ISO timestamp format"):
            parse_iso_timestamp("invalid-timestamp")

    def test_parse_none_input(self) -> None:
        """Test parsing None input raises ValueError."""
        with pytest.raises(ValueError, match="Timestamp string cannot be empty"):
            parse_iso_timestamp(None)  # type: ignore[arg-type]


class TestNowUtc:
    """Test UTC current time function."""

    def test_returns_utc_timezone(self) -> None:
        """Test that now_utc returns UTC timezone."""
        result = now_utc()
        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self) -> None:
        """Test that now_utc returns approximately current time."""
        before = datetime.now(timezone.utc)
        result = now_utc()
        after = datetime.now(timezone.utc)

        # Should be between before and after (allowing for execution time)
        assert before <= result <= after


class TestFormatForCache:
    """Test cache formatting."""

    def test_format_utc_datetime(self) -> None:
        """Test formatting UTC datetime for cache."""
        dt = datetime(2026, 1, 3, 23, 36, 14, 620992, timezone.utc)
        result = format_for_cache(dt)

        expected = "2026-01-03T23:36:14.620992+00:00"
        assert result == expected

    def test_format_datetime_with_offset(self) -> None:
        """Test formatting datetime with timezone offset for cache."""
        cet_tz = timezone(timedelta(hours=1))
        dt = datetime(2026, 1, 3, 23, 36, 14, 620992, cet_tz)
        result = format_for_cache(dt)

        expected = "2026-01-03T23:36:14.620992+01:00"
        assert result == expected

    def test_format_naive_datetime_raises(self) -> None:
        """Test formatting naive datetime raises ValueError."""
        dt = datetime(2026, 1, 3, 23, 36, 14)
        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            format_for_cache(dt)

