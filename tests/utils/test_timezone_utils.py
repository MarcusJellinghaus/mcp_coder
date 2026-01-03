"""Unit tests for timezone utilities."""

from datetime import datetime, timedelta, timezone

import pytest

from mcp_coder.utils.timezone_utils import (
    calculate_elapsed_seconds,
    ensure_timezone_aware,
    format_for_cache,
    format_for_github_api,
    is_within_duration,
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


class TestFormatForGithubApi:
    """Test GitHub API formatting."""

    def test_format_utc_datetime(self) -> None:
        """Test formatting UTC datetime."""
        dt = datetime(2026, 1, 3, 23, 36, 14, 620992, timezone.utc)
        result = format_for_github_api(dt)

        expected = "2026-01-03T23:36:14.620992Z"
        assert result == expected

    def test_format_datetime_with_offset(self) -> None:
        """Test formatting datetime with timezone offset."""
        # CET timezone (+01:00)
        cet_tz = timezone(timedelta(hours=1))
        dt = datetime(2026, 1, 3, 23, 36, 14, 620992, cet_tz)
        result = format_for_github_api(dt)

        # Should be converted to UTC
        expected = "2026-01-03T22:36:14.620992Z"
        assert result == expected

    def test_format_naive_datetime_raises(self) -> None:
        """Test formatting naive datetime raises ValueError."""
        dt = datetime(2026, 1, 3, 23, 36, 14)
        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            format_for_github_api(dt)


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


class TestEnsureTimezoneAware:
    """Test timezone awareness enforcement."""

    def test_naive_datetime_assume_utc(self) -> None:
        """Test naive datetime assumed as UTC."""
        dt = datetime(2026, 1, 3, 23, 36, 14)
        result = ensure_timezone_aware(dt, assume_utc=True)

        expected = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        assert result == expected

    def test_naive_datetime_assume_local(self) -> None:
        """Test naive datetime with local timezone."""
        dt = datetime(2026, 1, 3, 23, 36, 14)
        result = ensure_timezone_aware(dt, assume_utc=False)

        # Should have some timezone (depends on system)
        assert result.tzinfo is not None
        assert result.hour == 23  # Time unchanged, only timezone added

    def test_aware_datetime_unchanged(self) -> None:
        """Test timezone-aware datetime is unchanged."""
        dt = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        result = ensure_timezone_aware(dt)

        assert result == dt
        assert result.tzinfo == timezone.utc


class TestCalculateElapsedSeconds:
    """Test elapsed time calculations."""

    def test_calculate_elapsed_same_timezone(self) -> None:
        """Test elapsed calculation with same timezone."""
        start = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        end = datetime(2026, 1, 3, 23, 37, 14, 0, timezone.utc)
        result = calculate_elapsed_seconds(start, end)

        assert result == 60.0

    def test_calculate_elapsed_different_timezones(self) -> None:
        """Test elapsed calculation with different timezones."""
        start = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        # 1 minute later in CET (which is same UTC time + 1 hour)
        cet_tz = timezone(timedelta(hours=1))
        end = datetime(2026, 1, 4, 0, 37, 14, 0, cet_tz)  # Same as 23:37 UTC
        result = calculate_elapsed_seconds(start, end)

        assert result == 60.0

    def test_calculate_elapsed_to_now(self) -> None:
        """Test elapsed calculation to current time."""
        start = datetime.now(timezone.utc) - timedelta(seconds=5)
        result = calculate_elapsed_seconds(start)

        # Should be approximately 5 seconds (allowing for execution time)
        assert 4.0 <= result <= 6.0

    def test_naive_start_time_raises(self) -> None:
        """Test naive start time raises ValueError."""
        start = datetime(2026, 1, 3, 23, 36, 14)
        end = datetime(2026, 1, 3, 23, 37, 14, 0, timezone.utc)

        with pytest.raises(ValueError, match="start_time must be timezone-aware"):
            calculate_elapsed_seconds(start, end)

    def test_naive_end_time_raises(self) -> None:
        """Test naive end time raises ValueError."""
        start = datetime(2026, 1, 3, 23, 36, 14, 0, timezone.utc)
        end = datetime(2026, 1, 3, 23, 37, 14)

        with pytest.raises(ValueError, match="end_time must be timezone-aware"):
            calculate_elapsed_seconds(start, end)


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

        # Format for GitHub API
        github_format = format_for_github_api(parsed)
        assert github_format == "2026-01-03T22:36:14.620992Z"

        # Format for cache
        cache_format = format_for_cache(parsed)
        assert cache_format == "2026-01-03T22:36:14.620992+00:00"

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

        # Verify GitHub API would get correct timestamp
        github_since = format_for_github_api(cache_time)
        assert github_since == "2026-01-03T22:36:14.620992Z"

        # Verify user change in UTC is after GitHub since parameter
        user_change_utc_str = format_for_github_api(user_change)
        assert user_change_utc_str == "2026-01-03T23:00:00Z"

        # Parse GitHub format and verify comparison
        github_since_dt = parse_iso_timestamp(github_since)
        user_change_utc_dt = parse_iso_timestamp(user_change_utc_str)
        assert user_change_utc_dt > github_since_dt
