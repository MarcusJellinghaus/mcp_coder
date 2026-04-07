"""Unit tests for set_status --from-status precondition flag.

Split from test_set_status.py to keep file sizes under the 750-line limit.
"""

import argparse
import logging
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.set_status import execute_set_status


@pytest.fixture
def full_labels_config(labels_config_path: Path) -> Dict[str, Any]:
    """Load labels configuration from actual config file.

    Args:
        labels_config_path: Path to labels.json from conftest fixture

    Returns:
        Dict with 'workflow_labels' matching the structure from config/labels.json
    """
    from mcp_coder.utils.github_operations.label_config import load_labels_config

    return load_labels_config(labels_config_path)


@pytest.fixture
def mock_issue_manager() -> MagicMock:
    """Mock IssueManager for GitHub operations.

    Returns:
        MagicMock configured to simulate IssueManager behavior
    """
    mock = MagicMock()

    # Configure mock to return issue data
    mock.get_issue.return_value = {
        "number": 123,
        "title": "Test Issue",
        "body": "Test body",
        "state": "open",
        "labels": ["status-03:planning", "bug"],
        "assignees": [],
        "user": "testuser",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "url": "https://github.com/test/repo/issues/123",
        "locked": False,
    }

    # Configure mock to return success for set_labels
    mock.set_labels.return_value = {
        "number": 123,
        "title": "Test Issue",
        "body": "Test body",
        "state": "open",
        "labels": ["status-05:plan-ready", "bug"],
        "assignees": [],
        "user": "testuser",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "url": "https://github.com/test/repo/issues/123",
        "locked": False,
    }

    return mock


class TestFromStatusFlag:
    """Tests for --from-status precondition flag."""

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_matching_updates_label(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Current label matches --from-status -> update proceeds, exit 0."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = True

        # Issue currently has status-03:planning
        mock_issue_manager.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": ["status-03:planning", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "locked": False,
        }

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=False,
            from_status="status-03:planning",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 0
        assert "Updated issue #123 to status-05:plan-ready" in caplog.text
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_mismatch_skips_with_message(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Current label differs from --from-status -> no set_labels, skip message, exit 0."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = True

        # Issue currently has status-07:code-review, NOT status-06:implementing
        mock_issue_manager.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "locked": False,
        }

        args = argparse.Namespace(
            status_label="status-06f:implementing-failed",
            issue=123,
            project_dir=str(project_dir),
            force=False,
            from_status="status-06:implementing",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 0
        mock_issue_manager.set_labels.assert_not_called()
        assert "Skipped set-status to 'status-06f:implementing-failed'" in caplog.text
        assert "expected 'status-06:implementing'" in caplog.text

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_no_current_label_skips(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Issue has no status label -> no-op, <none> in skip message, exit 0."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = True

        # Issue has no status labels
        mock_issue_manager.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "locked": False,
        }

        args = argparse.Namespace(
            status_label="status-06f:implementing-failed",
            issue=123,
            project_dir=str(project_dir),
            force=False,
            from_status="status-06:implementing",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 0
        mock_issue_manager.set_labels.assert_not_called()
        assert "'<none>'" in caplog.text

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_invalid_value_returns_error(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """--from-status value not in labels.json -> exit 1."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_is_working_directory_clean.return_value = True

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=False,
            from_status="invalid-label",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 1
        assert "invalid-label" in caplog.text.lower()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_combined_with_force_and_issue(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """--from-status + --force + --issue all work together."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager

        # Issue currently has matching label
        mock_issue_manager.get_issue.return_value = {
            "number": 456,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": ["status-06:implementing"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://github.com/test/repo/issues/456",
            "locked": False,
        }

        args = argparse.Namespace(
            status_label="status-06f:implementing-failed",
            issue=456,
            project_dir=str(project_dir),
            force=True,
            from_status="status-06:implementing",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 0
        assert "Updated issue #456 to status-06f:implementing-failed" in caplog.text
        mock_issue_manager.set_labels.assert_called_once()
        # Force bypasses working directory check
        mock_is_working_directory_clean.assert_not_called()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_no_extra_api_call(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify get_issue is called exactly once (reuses existing fetch)."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = True

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=False,
            from_status="status-03:planning",
        )

        with caplog.at_level(logging.DEBUG):
            execute_set_status(args)

        mock_issue_manager.get_issue.assert_called_once_with(123)

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_skip_does_not_log_updated_message(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """On skip path, only skip message appears, NOT 'Updated issue'."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = True

        # Mismatch: issue has status-07, but from_status expects status-06
        mock_issue_manager.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "locked": False,
        }

        args = argparse.Namespace(
            status_label="status-06f:implementing-failed",
            issue=123,
            project_dir=str(project_dir),
            force=False,
            from_status="status-06:implementing",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 0
        assert "Skipped set-status" in caplog.text
        assert "Updated issue" not in caplog.text

    def test_from_status_without_positional_label_errors(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """set-status --from-status foo with no positional exits with code 2."""
        args = argparse.Namespace(
            status_label=None,
            issue=123,
            project_dir=None,
            force=False,
            from_status="status-06:implementing",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 2
        assert "--from-status requires a positional status_label" in caplog.text

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_from_status_force_dirty_wd_mismatch_skips_silently(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """--from-status + --force + dirty wd + mismatch -> exit 0, skip msg, no dirty-wd warning."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = False  # Dirty wd

        # Mismatch: issue already past in-progress
        mock_issue_manager.get_issue.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "locked": False,
        }

        args = argparse.Namespace(
            status_label="status-06f:implementing-failed",
            issue=123,
            project_dir=str(project_dir),
            force=True,
            from_status="status-06:implementing",
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_set_status(args)

        assert result == 0
        assert "Skipped set-status" in caplog.text
        assert "uncommitted changes" not in caplog.text.lower()
        mock_issue_manager.set_labels.assert_not_called()
