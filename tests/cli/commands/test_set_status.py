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
    format_status_labels,
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
    "status-03f:planning-failed",
    "status-06f:implementing-failed",
    "status-06f-ci:ci-fix-needed",
    "status-06f-timeout:llm-timeout",
    "status-09f:pr-creating-failed",
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


class TestSetStatusHelpers:
    """Test helper functions."""

    def test_format_status_labels_output(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test format_status_labels contains header, all labels, and descriptions."""
        result = format_status_labels(full_labels_config)

        # Verify header
        assert result.startswith("Available status labels:")

        # Verify all label names and descriptions are present
        for label in full_labels_config["workflow_labels"]:
            assert label["name"] in result, f"Label '{label['name']}' missing"
            assert (
                label["description"] in result
            ), f"Description for '{label['name']}' missing"

        # Verify alignment: all description starts should be at the same column
        lines = result.split("\n")
        label_lines = [line for line in lines if line.startswith("  ")]
        assert len(label_lines) == len(full_labels_config["workflow_labels"])

    def test_format_status_labels_dynamic_width(
        self,
    ) -> None:
        """Test column width adapts to label name length."""
        short_config = {
            "workflow_labels": [
                {"name": "a", "description": "short"},
                {"name": "bb", "description": "medium"},
            ]
        }
        long_config = {
            "workflow_labels": [
                {"name": "very-long-label-name", "description": "desc1"},
                {"name": "x", "description": "desc2"},
            ]
        }

        short_result = format_status_labels(short_config)
        long_result = format_status_labels(long_config)

        # In short_config, max name length is 2, so width = 4
        # "bb" line should have the name padded to width 4
        short_lines = short_result.split("\n")
        # Find line with "a" - it should be padded to same width as "bb"
        a_line = [l for l in short_lines if "short" in l][0]
        bb_line = [l for l in short_lines if "medium" in l][0]
        # Both descriptions should start at the same column
        assert a_line.index("short") == bb_line.index("medium")

        # In long_config, max name length is 20, so width = 22
        long_lines = long_result.split("\n")
        desc1_line = [l for l in long_lines if "desc1" in l][0]
        desc2_line = [l for l in long_lines if "desc2" in l][0]
        assert desc1_line.index("desc1") == desc2_line.index("desc2")

        # The description column should be further right in long_config
        assert desc1_line.index("desc1") > a_line.index("short")

    def test_format_status_labels_empty_workflow_labels(self) -> None:
        """Test format_status_labels returns fallback for empty workflow_labels."""
        empty_config: Dict[str, Any] = {"workflow_labels": []}
        result = format_status_labels(empty_config)
        assert result == "No labels configured."

    def test_validate_status_label_valid(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test validation accepts valid status labels."""
        # Test each valid label
        for label_name in VALID_STATUS_LABELS:
            is_valid, error = validate_status_label(label_name, full_labels_config)
            assert is_valid is True, f"Label '{label_name}' should be valid"
            assert error is None

    def test_validate_status_label_invalid(
        self, full_labels_config: Dict[str, Any]
    ) -> None:
        """Test validation rejects invalid labels with descriptive error."""
        # Test invalid labels
        invalid_labels = [
            "invalid-label",
            "status-99:nonexistent",
            "bug",
            "enhancement",
            "",
        ]

        for label_name in invalid_labels:
            is_valid, error = validate_status_label(label_name, full_labels_config)
            assert is_valid is False, f"Label '{label_name}' should be invalid"
            assert error is not None
            # Error should contain label descriptions (from format_status_labels)
            first_label = full_labels_config["workflow_labels"][0]
            assert first_label["description"] in error


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

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_set_status_no_args_shows_labels(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_is_working_directory_clean: MagicMock,
        tmp_path: Path,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test no-args prints available labels and returns 0."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config

        args = argparse.Namespace(
            status_label=None,
            issue=None,
            project_dir=str(project_dir),
            force=False,
        )

        result = execute_set_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Available status labels" in captured.out
        # Verify no side effects occurred
        mock_is_working_directory_clean.assert_not_called()
        mock_issue_manager_class.assert_not_called()

    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_set_status_no_args_malformed_config_fallback(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Test no-args falls back to bundled config when load_labels_config fails."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        project_config = project_dir / "config" / "labels.json"
        bundled_config = Path("/bundled/labels.json")
        mock_get_config_path.side_effect = [project_config, bundled_config]
        # First call (project config) fails, second call (bundled) succeeds
        mock_load_config.side_effect = [ValueError("malformed"), full_labels_config]

        args = argparse.Namespace(
            status_label=None,
            issue=None,
            project_dir=str(project_dir),
            force=False,
        )

        result = execute_set_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Available status labels" in captured.out
        # Verify it fell back to bundled config
        mock_get_config_path.assert_called_with(None)

    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_set_status_no_args_fallback_config(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        full_labels_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test no-args falls back to bundled config when project dir fails."""
        mock_resolve_dir.side_effect = ValueError("No project dir")
        mock_get_config_path.return_value = Path("/fallback/labels.json")
        mock_load_config.return_value = full_labels_config

        args = argparse.Namespace(
            status_label=None,
            issue=None,
            project_dir=None,
            force=False,
        )

        result = execute_set_status(args)

        assert result == 0
        # Should have called get_labels_config_path with None (fallback)
        mock_get_config_path.assert_called_with(None)
        captured = capsys.readouterr()
        assert "Available status labels" in captured.out

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
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
        mock_is_working_directory_clean: MagicMock,
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
        mock_is_working_directory_clean.return_value = True

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=None,
            project_dir=str(project_dir),
            force=False,
        )

        result = execute_set_status(args)

        assert result == 0
        mock_extract_issue.assert_called_once_with("123-feature-name")
        mock_issue_manager.get_issue.assert_called_once_with(123)
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
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
        mock_is_working_directory_clean: MagicMock,
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
        mock_is_working_directory_clean.return_value = True

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=False,
        )

        result = execute_set_status(args)

        assert result == 0
        # Should use explicit issue number, not branch detection
        mock_issue_manager.get_issue.assert_called_once_with(123)
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_invalid_label_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_is_working_directory_clean: MagicMock,
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
        mock_is_working_directory_clean.return_value = True

        args = argparse.Namespace(
            status_label="invalid-label",
            issue=123,
            project_dir=str(project_dir),
            force=False,
        )

        result = execute_set_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "invalid" in captured.err.lower()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
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
        mock_is_working_directory_clean: MagicMock,
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
        mock_is_working_directory_clean.return_value = True

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=None,  # No explicit issue
            project_dir=str(project_dir),
            force=False,
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

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
    @patch("mcp_coder.cli.commands.set_status.IssueManager")
    @patch("mcp_coder.cli.commands.set_status.load_labels_config")
    @patch("mcp_coder.cli.commands.set_status.get_labels_config_path")
    @patch("mcp_coder.cli.commands.set_status.resolve_project_dir")
    def test_execute_set_status_clean_directory_succeeds(
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
        """Test that set-status succeeds when working directory is clean."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = full_labels_config
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_is_working_directory_clean.return_value = True  # Clean directory

        args = argparse.Namespace(
            status_label="status-05:plan-ready",
            issue=123,
            project_dir=str(project_dir),
            force=False,  # No force flag
        )

        result = execute_set_status(args)

        assert result == 0
        # With clean directory, is_working_directory_clean should be called
        mock_is_working_directory_clean.assert_called_once()
        mock_issue_manager.get_issue.assert_called_once_with(123)
        mock_issue_manager.set_labels.assert_called_once()

    @patch("mcp_coder.cli.commands.set_status.is_working_directory_clean")
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
        mock_is_working_directory_clean: MagicMock,
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
        mock_is_working_directory_clean.return_value = True

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
            force=False,
        )

        result = execute_set_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err or "failed" in captured.err.lower()
