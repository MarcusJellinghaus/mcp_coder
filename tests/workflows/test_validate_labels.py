"""
Unit tests for workflows/validate_labels.py module.

Tests cover argument parsing, STALE_TIMEOUTS constant, and basic setup logic.
"""

from datetime import datetime, timedelta, timezone

import pytest

from workflows.validate_labels import (
    STALE_TIMEOUTS,
    calculate_elapsed_minutes,
    parse_arguments,
)


def test_stale_timeouts_defined() -> None:
    """Test that timeout constants are properly defined."""
    assert STALE_TIMEOUTS["implementing"] == 60
    assert STALE_TIMEOUTS["planning"] == 15
    assert STALE_TIMEOUTS["pr_creating"] == 15


def test_parse_arguments_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test argument parser with default values."""
    # Simulate command line with no arguments (just script name)
    monkeypatch.setattr("sys.argv", ["validate_labels.py"])

    args = parse_arguments()

    # Verify defaults
    assert args.project_dir is None
    assert args.log_level == "INFO"
    assert args.dry_run is False


def test_parse_arguments_with_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --dry-run flag parsing."""
    # Simulate command line with --dry-run flag
    monkeypatch.setattr("sys.argv", ["validate_labels.py", "--dry-run"])

    args = parse_arguments()

    assert args.dry_run is True


def test_parse_arguments_with_project_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --project-dir argument parsing."""
    test_path = "/path/to/project"
    monkeypatch.setattr("sys.argv", ["validate_labels.py", "--project-dir", test_path])

    args = parse_arguments()

    assert args.project_dir == test_path


def test_parse_arguments_with_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --log-level argument parsing."""
    monkeypatch.setattr("sys.argv", ["validate_labels.py", "--log-level", "DEBUG"])

    args = parse_arguments()

    assert args.log_level == "DEBUG"


def test_parse_arguments_all_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test all command-line arguments together."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_labels.py",
            "--project-dir",
            "/test/path",
            "--log-level",
            "ERROR",
            "--dry-run",
        ],
    )

    args = parse_arguments()

    assert args.project_dir == "/test/path"
    assert args.log_level == "ERROR"
    assert args.dry_run is True


def test_calculate_elapsed_minutes_with_z_suffix() -> None:
    """Test calculate_elapsed_minutes with 'Z' suffix timestamp."""
    # Create a timestamp 30 minutes ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 30 minutes (allow ±1 minute for test execution time)
    assert 29 <= elapsed <= 31


def test_calculate_elapsed_minutes_without_z_suffix() -> None:
    """Test calculate_elapsed_minutes with UTC offset format."""
    # Create a timestamp 45 minutes ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=45)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 45 minutes (allow ±1 minute for test execution time)
    assert 44 <= elapsed <= 46


def test_calculate_elapsed_minutes_recent_timestamp() -> None:
    """Test calculate_elapsed_minutes with very recent timestamp."""
    # Create a timestamp just a few seconds ago
    past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be 0 minutes (30 seconds rounds down to 0)
    assert elapsed == 0


def test_calculate_elapsed_minutes_one_hour_ago() -> None:
    """Test calculate_elapsed_minutes with timestamp one hour ago."""
    # Create a timestamp 60 minutes ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 60 minutes (allow ±1 minute for test execution time)
    assert 59 <= elapsed <= 61


def test_calculate_elapsed_minutes_multiple_hours() -> None:
    """Test calculate_elapsed_minutes with timestamp several hours ago."""
    # Create a timestamp 150 minutes (2.5 hours) ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=150)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 150 minutes (allow ±1 minute for test execution time)
    assert 149 <= elapsed <= 151


def test_calculate_elapsed_minutes_with_microseconds() -> None:
    """Test calculate_elapsed_minutes with timestamp containing microseconds."""
    # Create a timestamp 20 minutes ago with microseconds
    past_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 20 minutes (allow ±1 minute for test execution time)
    assert 19 <= elapsed <= 21
