"""
Unit tests for workflows/validate_labels.py module.

Tests cover argument parsing, STALE_TIMEOUTS constant, and basic setup logic.
"""

import pytest

from workflows.validate_labels import STALE_TIMEOUTS, parse_arguments


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
