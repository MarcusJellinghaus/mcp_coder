"""Unit tests for set_status CLI command module.

Tests cover:
- Helper functions (status label validation, config loading)
- Label computation logic (compute_new_labels)
- CLI execute function (execute_set_status)
"""

import argparse
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.set_status import (
    compute_new_labels,
    execute_set_status,
    get_status_labels_from_config,
    validate_status_label,
)

# Note: labels_config_path fixture is defined in tests/conftest.py


# Test data constants
VALID_STATUS_LABELS = [
    "status-01:created",
    "status-02:awaiting-planning",
    "status-03:planning",
    "status-04:plan-review",
    "status-05:plan-ready",
    "status-06:implementing",
    "status-07:code-review",
    "status-08:ready-pr",
    "status-09:pr-creating",
    "status-10:pr-created",
]


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


@pytest.fixture
def mock_is_working_directory_clean():
    """Mock is_working_directory_clean function."""
    with patch("mcp_coder.cli.commands.set_status.is_working_directory_clean") as mock:
        yield mock


class TestSetStatusHelpers:
    """Test helper functions."""

    def test_get_status_labels_from_config(self, labels_config_path: Path) -> None:
        """Test loading status labels from config."""
        # Load actual labels from config
        labels = get_status_labels_from_config(labels_config_path)

        # Verify we get a set of label names
        assert isinstance(labels, set)
        assert len(labels) == 10  # 10 workflow labels

        # Verify all labels start with 'status-'
        for label in labels:
            assert label.startswith(
                "status-"
            ), f"Label '{label}' should start with 'status-'"

    def test_validate_status_label_valid(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test validation accepts valid status labels."""
        all_status_labels = {
            label["name"] for label in full_labels_config["workflow_labels"]
        }

        # Test each valid label
        for label_name in VALID_STATUS_LABELS:
            is_valid, error = validate_status_label(label_name, all_status_labels)
            assert is_valid is True, f"Label '{label_name}' should be valid"
            assert error is None

    def test_validate_status_label_invalid(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test validation rejects invalid labels."""
        all_status_labels = {
            label["name"] for label in full_labels_config["workflow_labels"]
        }

        # Test invalid labels
        invalid_labels = [
            "invalid-label",
            "status-99:nonexistent",
            "bug",
            "enhancement",
            "",
        ]

        for label_name in invalid_labels:
            is_valid, error = validate_status_label(label_name, all_status_labels)
            assert is_valid is False, f"Label '{label_name}' should be invalid"
            assert error is not None


class TestComputeNewLabels:
    """Test label computation logic."""

    def test_compute_replaces_status_label(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test that existing status-* labels are replaced."""
        current_labels = {"status-03:planning", "bug", "enhancement"}
        new_status = "status-05:plan-ready"
        all_status_names = {
            label["name"] for label in full_labels_config["workflow_labels"]
        }

        result = compute_new_labels(current_labels, new_status, all_status_names)

        # Verify old status label removed and new one added
        assert "status-05:plan-ready" in result
        assert "status-03:planning" not in result
        # Verify non-status labels preserved
        assert "bug" in result
        assert "enhancement" in result

    def test_compute_preserves_non_status_labels(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test that non-status labels are preserved."""
        current_labels = {
            "status-06:implementing",
            "bug",
            "high-priority",
            "documentation",
        }
        new_status = "status-08:ready-pr"
        all_status_names = {
            label["name"] for label in full_labels_config["workflow_labels"]
        }

        result = compute_new_labels(current_labels, new_status, all_status_names)

        # Verify all non-status labels preserved
        assert "bug" in result
        assert "high-priority" in result
        assert "documentation" in result
        # Verify new status applied
        assert "status-08:ready-pr" in result
        # Verify old status removed
        assert "status-06:implementing" not in result

    def test_compute_with_no_existing_status(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test adding status when none exists."""
        current_labels = {"bug", "enhancement"}
        new_status = "status-01:created"
        all_status_names = {
            label["name"] for label in full_labels_config["workflow_labels"]
        }

        result = compute_new_labels(current_labels, new_status, all_status_names)

        # Verify new status added
        assert "status-01:created" in result
        # Verify existing labels preserved
        assert "bug" in result
        assert "enhancement" in result


class TestExecuteSetStatus:
    """Test CLI execute function."""

    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.set_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.set_status.extract_issue_number_from_branch")
    def test_execute_success_with_branch_detection(
        self,
        mock_extract_issue: MagicMock,
        mock_get_branch: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
    ) -> None:
        """Test successful execution with auto-detected issue."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_branch.return_value = "123-feature-name"
        mock_extract_issue.return_value = 123
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=None,
            project_dir=str(project_dir),
        )

        result = execute_set_status(args)

        assert result == 0
        mock_extract_issue.assert_called_once_with("123-feature-name")
        mock_issue_manager.get_issue.assert_called_once_with(123)
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_success_with_explicit_issue(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
    ) -> None:
        """Test successful execution with --issue flag."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
        )

        result = execute_set_status(args)

        assert result == 0
        # Should use explicit issue number, not branch detection
        mock_issue_manager.get_issue.assert_called_once_with(123)
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_invalid_label_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test invalid label name returns exit code 1."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config

        args = argparse.Namespace(
            status_label="invalid-label",
            issue=123,
            project_dir=str(project_dir),
        )

        result = execute_set_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "invalid" in captured.err.lower()

    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.set_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.set_status.extract_issue_number_from_branch")
    def test_execute_no_issue_detected_returns_one(
        self,
        mock_extract_issue: MagicMock,
        mock_get_branch: MagicMock,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test returns 1 when branch doesn't match pattern."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_branch.return_value = "feature-no-issue-number"
        mock_extract_issue.return_value = None  # No issue number in branch
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=None,  # No explicit issue
            project_dir=str(project_dir),
        )

        result = execute_set_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "issue" in captured.err.lower()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_set_status_dirty_directory_fails(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that set-status fails when working directory has uncommitted changes."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_is_working_directory_clean.return_value = False

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=False,
        )

        result = execute_set_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "uncommitted changes" in captured.err.lower()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_set_status_dirty_directory_with_force_succeeds(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        mock_issue_manager: MagicMock,
    ) -> None:
        """Test that set-status succeeds with --force even when directory is dirty."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = False  # Dirty directory

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=True,  # Force flag bypasses dirty check
        )

        result = execute_set_status(args)

        assert result == 0
        # With force=True, is_working_directory_clean should NOT be called
        mock_is_working_directory_clean.assert_not_called()
        mock_issue_manager.get_issue.assert_called_once_with(123)
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_github_error_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test returns 1 on GitHub API error."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config

        # Configure mock to return error (number=0 indicates error)
        mock_issue_manager = MagicMock()
        mock_issue_manager.get_issue.return_value = {
            "number": 0,  # Error indicator
            "title": "",
            "body": "",
            "state": "",
            "labels": [],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
        )

        result = execute_set_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "failed" in captured.err.lower()
