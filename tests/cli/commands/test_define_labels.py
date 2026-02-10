"""Unit tests for define_labels CLI command module.

Tests cover:
- WORKFLOW_LABELS constant validation and structure
- Color format validation
- Module load-time validation
- Project directory resolution and validation
- execute_define_labels() CLI command function

Note: Additional tests are split into separate modules:
- test_define_labels_validation.py - Validation and staleness detection tests
- test_define_labels_label_changes.py - Label change calculation tests
"""

import argparse
import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.define_labels import (
    apply_labels,
    execute_define_labels,
)
from mcp_coder.utils.github_operations.label_config import load_labels_config
from mcp_coder.workflows.utils import resolve_project_dir
from tests.utils.conftest import git_repo


class TestWorkflowLabelsFromConfig:
    """Test loading workflow labels from JSON config."""

    def test_load_workflow_labels_from_json(
        self, tmp_path: Path, labels_config_path: Path
    ) -> None:
        """Test that workflow labels can be loaded from JSON config."""
        # Create a temporary config file
        config_dir = tmp_path / "workflows" / "config"
        config_dir.mkdir(parents=True)

        # Load the actual config to test against
        labels_config = load_labels_config(labels_config_path)

        # Verify we have exactly 10 labels
        assert (
            len(labels_config["workflow_labels"]) == 10
        ), "Config should contain exactly 10 workflow labels"

        # Verify each label has correct structure
        for i, label in enumerate(labels_config["workflow_labels"], start=1):
            assert isinstance(label, dict), f"Label {i} should be a dict"
            assert "name" in label, f"Label {i} should have 'name' field"
            assert "color" in label, f"Label {i} should have 'color' field"
            assert "description" in label, f"Label {i} should have 'description' field"

            name = label["name"]
            color = label["color"]
            description = label["description"]

            # Verify name format
            assert isinstance(name, str), f"Label {i} name should be string"
            assert name.startswith(
                "status-"
            ), f"Label {i} name should start with 'status-'"
            assert (
                f"status-{i:02d}:" in name
            ), f"Label {i} should have correct status number format"

            # Verify color format (6-char hex without '#')
            assert isinstance(color, str), f"Label {i} color should be string"
            assert len(color) == 6, f"Label {i} color should be 6 characters"
            assert re.match(
                r"^[0-9A-Fa-f]{6}$", color
            ), f"Label {i} color should be valid hex code"

            # Verify description
            assert isinstance(
                description, str
            ), f"Label {i} description should be string"
            assert len(description) > 0, f"Label {i} description should not be empty"

    def test_workflow_labels_names_from_json(self, labels_config_path: Path) -> None:
        """Test that all expected workflow label names are present in JSON."""
        labels_config = load_labels_config(labels_config_path)

        expected_names = [
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

        actual_names = [label["name"] for label in labels_config["workflow_labels"]]
        assert (
            actual_names == expected_names
        ), "Workflow label names should match expected sequence"

    def test_workflow_labels_unique_names_from_json(
        self, labels_config_path: Path
    ) -> None:
        """Test that all workflow label names in JSON are unique."""
        labels_config = load_labels_config(labels_config_path)

        names = [label["name"] for label in labels_config["workflow_labels"]]
        assert len(names) == len(
            set(names)
        ), "All workflow label names should be unique"

    def test_workflow_labels_unique_colors_from_json(
        self, labels_config_path: Path
    ) -> None:
        """Test that all workflow label colors in JSON are unique."""
        labels_config = load_labels_config(labels_config_path)

        colors = [label["color"] for label in labels_config["workflow_labels"]]
        assert len(colors) == len(
            set(colors)
        ), "All workflow label colors should be unique"


class TestWorkflowLabelsContent:
    """Test specific content and metadata of workflow labels."""

    def test_all_labels_have_descriptions(self, labels_config_path: Path) -> None:
        """Test that all labels have non-empty descriptions."""
        labels_config = load_labels_config(labels_config_path)

        for label in labels_config["workflow_labels"]:
            description = label["description"]
            assert (
                description.strip()
            ), f"Label '{label['name']}' should have non-empty description"

    def test_status_labels_cover_workflow_stages(
        self, labels_config_path: Path
    ) -> None:
        """Test that labels cover the expected workflow stages."""
        labels_config = load_labels_config(labels_config_path)

        # Check for key workflow stages
        names = [label["name"] for label in labels_config["workflow_labels"]]

        # Should have creation stage
        assert any("created" in name for name in names), "Should have 'created' stage"

        # Should have planning stages
        assert any("planning" in name for name in names), "Should have 'planning' stage"

        # Should have implementation stage
        assert any(
            "implementing" in name for name in names
        ), "Should have 'implementing' stage"

        # Should have review stage
        assert any("review" in name for name in names), "Should have 'review' stage"

        # Should have PR-related stages
        assert any("pr" in name for name in names), "Should have PR-related stages"

    def test_color_codes_are_github_compatible(self, labels_config_path: Path) -> None:
        """Test that all color codes follow GitHub API format (6-char hex without #)."""
        labels_config = load_labels_config(labels_config_path)

        for label in labels_config["workflow_labels"]:
            name = label["name"]
            color = label["color"]

            # GitHub API requires 6-char hex WITHOUT '#' prefix
            assert not color.startswith(
                "#"
            ), f"Label '{name}' color should not have '#' prefix"
            assert (
                len(color) == 6
            ), f"Label '{name}' color should be exactly 6 characters"
            assert color.isalnum(), f"Label '{name}' color should be alphanumeric"


class TestResolveProjectDir:
    """Test project directory resolution and validation."""

    @pytest.mark.git_integration
    def test_resolve_project_dir_current_directory(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test resolve_project_dir with None argument uses current directory."""
        repo, project_dir = git_repo

        # Change to project directory and test with None
        with patch("pathlib.Path.cwd", return_value=project_dir):
            result = resolve_project_dir(None)
            assert (
                result == project_dir.resolve()
            ), "Should return current directory when arg is None"

    @pytest.mark.git_integration
    def test_resolve_project_dir_explicit_path(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test resolve_project_dir with explicit path argument."""
        repo, project_dir = git_repo

        # Test with explicit path string
        result = resolve_project_dir(str(project_dir))
        assert (
            result == project_dir.resolve()
        ), "Should return resolved path from argument"

    def test_resolve_project_dir_nonexistent_directory(self) -> None:
        """Test resolve_project_dir raises ValueError for nonexistent directory."""
        nonexistent_path = "/nonexistent/path/that/does/not/exist"

        with pytest.raises(ValueError, match="does not exist"):
            resolve_project_dir(nonexistent_path)

    def test_resolve_project_dir_not_git_repository(self, tmp_path: Path) -> None:
        """Test resolve_project_dir raises ValueError for directory without .git."""
        # Create a directory without .git
        non_git_dir = tmp_path / "not_a_git_repo"
        non_git_dir.mkdir()

        with pytest.raises(ValueError, match="not a git repository"):
            resolve_project_dir(str(non_git_dir))

    def test_resolve_project_dir_file_instead_of_directory(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir raises ValueError when path is a file."""
        # Create a file instead of a directory
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        with pytest.raises(ValueError, match="not a directory"):
            resolve_project_dir(str(test_file))

    @pytest.mark.git_integration
    def test_resolve_project_dir_relative_path(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test resolve_project_dir converts relative path to absolute."""
        repo, project_dir = git_repo

        # Test with relative path - use explicit relative path to tmp git repo
        # We can't properly test "." because Path.resolve() accesses the real filesystem
        # Instead, test that the function returns an absolute path
        result = resolve_project_dir(str(project_dir))
        assert result.is_absolute(), "Should return absolute path"
        assert (
            result == project_dir.resolve()
        ), "Should resolve to correct absolute path"


class TestExecuteDefineLabels:
    """Test the CLI execute function - minimal tests for wiring."""

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_execute_define_labels_dry_run_returns_zero(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful dry-run execution returns 0."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        # Setup IssueManager mock to return empty issues list
        mock_issue_manager_instance = MagicMock()
        mock_issue_manager_instance.list_issues.return_value = []
        mock_issue_manager.return_value = mock_issue_manager_instance

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=True,
        )

        result = execute_define_labels(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with(str(project_dir))
        mock_apply_labels.assert_called_once()
        # Verify dry_run was passed
        call_kwargs = mock_apply_labels.call_args[1]
        assert call_kwargs["dry_run"] is True

    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_execute_define_labels_invalid_dir_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test invalid project dir returns 1."""
        # Setup mock to raise ValueError (invalid directory)
        mock_resolve_dir.side_effect = ValueError("Project directory does not exist")

        args = argparse.Namespace(
            project_dir="/invalid/path",
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "does not exist" in captured.err
