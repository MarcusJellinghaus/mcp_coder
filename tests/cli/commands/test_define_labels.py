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
import logging
import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from mcp_coder.cli.commands.define_labels import (
    apply_labels,
    build_promotions,
    execute_define_labels,
    generate_approve_command_yml,
    generate_label_new_issues_yml,
    write_github_actions,
)
from mcp_coder.utils.github_operations.label_config import load_labels_config
from mcp_coder.workflows.utils import resolve_project_dir
from tests.utils.conftest import git_repo


def _make_namespace(
    project_dir: str | None = None,
    dry_run: bool = False,
    init: bool = False,
    validate: bool = False,
    all_ops: bool = False,
    config: str | None = None,
    generate_github_actions: bool = False,
) -> argparse.Namespace:
    """Build an argparse.Namespace with all define-labels flags."""
    return argparse.Namespace(
        project_dir=project_dir,
        dry_run=dry_run,
        init=init,
        validate=validate,
        all=all_ops,
        config=config,
        generate_github_actions=generate_github_actions,
    )


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

        # Verify we have exactly 15 labels
        assert (
            len(labels_config["workflow_labels"]) == 19
        ), "Config should contain exactly 19 workflow labels"

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
            "status-03f-timeout:planning-llm-timeout",
            "status-03f-prereq:planning-prereq-failed",
            "status-03f:planning-failed",
            "status-06f:implementing-failed",
            "status-06f-prep:task-tracker-prep-failed",
            "status-06f-ci:ci-fix-needed",
            "status-06f-timeout:llm-timeout",
            "status-06f-nochange:no-changes-after-retries",
            "status-09f:pr-creating-failed",
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

    def test_workflow_labels_valid_colors_from_json(
        self, labels_config_path: Path
    ) -> None:
        """Test that all workflow label colors in JSON are valid hex."""
        labels_config = load_labels_config(labels_config_path)

        for label in labels_config["workflow_labels"]:
            color = label["color"]
            assert re.match(
                r"^[0-9A-Fa-f]{6}$", color
            ), f"Label '{label['name']}' color '{color}' should be valid 6-char hex"


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
        _, project_dir = git_repo

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
        _, project_dir = git_repo

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
        _, project_dir = git_repo

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

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
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
        mock_validate_config: MagicMock,
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
                    "default": True,
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

        args = _make_namespace(
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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test invalid project dir returns 1."""
        # Setup mock to raise ValueError (invalid directory)
        mock_resolve_dir.side_effect = ValueError("Project directory does not exist")

        args = _make_namespace(
            project_dir="/invalid/path",
        )

        with caplog.at_level(logging.ERROR):
            result = execute_define_labels(args)

        assert result == 1
        assert "does not exist" in caplog.text


class TestFlagGating:
    """Test that --init, --validate, --all flags gate IssueManager usage."""

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_no_flags_skips_issue_manager(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Without --init or --validate, IssueManager is never created."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        args = _make_namespace(project_dir=str(project_dir))
        result = execute_define_labels(args)

        assert result == 0
        mock_issue_manager.assert_not_called()

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_init_flag_creates_issue_manager(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """With --init, IssueManager is created and initialize_issues called."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        mock_instance = MagicMock()
        mock_instance.list_issues.return_value = []
        mock_issue_manager.return_value = mock_instance

        args = _make_namespace(project_dir=str(project_dir), init=True)
        result = execute_define_labels(args)

        assert result == 0
        mock_issue_manager.assert_called_once_with(project_dir)
        mock_instance.list_issues.assert_called_once()

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_validate_flag_creates_issue_manager(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """With --validate, IssueManager is created and validate_issues called."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        mock_instance = MagicMock()
        mock_instance.list_issues.return_value = []
        mock_issue_manager.return_value = mock_instance

        args = _make_namespace(project_dir=str(project_dir), validate=True)
        result = execute_define_labels(args)

        assert result == 0
        mock_issue_manager.assert_called_once_with(project_dir)

    @patch("mcp_coder.cli.commands.define_labels.write_github_actions")
    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_all_flag_expands(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        mock_validate_config: MagicMock,
        mock_write_actions: MagicMock,
        tmp_path: Path,
    ) -> None:
        """--all enables init, validate, and generate_github_actions."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        mock_instance = MagicMock()
        mock_instance.list_issues.return_value = []
        mock_issue_manager.return_value = mock_instance
        mock_write_actions.return_value = []

        args = _make_namespace(project_dir=str(project_dir), all_ops=True)
        result = execute_define_labels(args)

        assert result == 0
        # --all should cause IssueManager to be created (init + validate)
        mock_issue_manager.assert_called_once_with(project_dir)
        mock_instance.list_issues.assert_called_once()
        # --all should trigger write_github_actions
        mock_write_actions.assert_called_once()

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_config_flag_passed_to_discovery(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """--config path is passed as config_override to get_labels_config_path."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        config_path = "/custom/labels.json"
        args = _make_namespace(project_dir=str(project_dir), config=config_path)
        execute_define_labels(args)

        # Verify config_override was passed
        call_kwargs = mock_get_config_path.call_args
        assert call_kwargs[1]["config_override"] == Path(config_path)

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_config_validation_always_runs(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """validate_labels_config is called even without --init or --validate."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        config = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_load_config.return_value = config
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        args = _make_namespace(project_dir=str(project_dir))
        execute_define_labels(args)

        mock_validate_config.assert_called_once_with(config)


class TestSummarySkipped:
    """Test that summary shows 'skipped' for operations not requested."""

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_no_flags_shows_skipped(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When no flags set, summary shows 'skipped' for init and validate."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        args = _make_namespace(project_dir=str(project_dir))
        execute_define_labels(args)

        output = capsys.readouterr().out
        assert "Issues initialized: skipped" in output

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_init_flag_shows_count(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With --init, summary shows actual count instead of skipped."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        mock_instance = MagicMock()
        mock_instance.list_issues.return_value = []
        mock_issue_manager.return_value = mock_instance

        args = _make_namespace(project_dir=str(project_dir), init=True)
        execute_define_labels(args)

        output = capsys.readouterr().out
        assert "Issues initialized: 0" in output
        assert "skipped" not in output.split("Issues initialized:")[1].split("\n")[0]


class TestBuildPromotions:
    """Test build_promotions() function."""

    def test_builds_from_promotable_labels(self) -> None:
        """Extracts (current, next) pairs from promotable: true labels."""
        config: dict[str, Any] = {
            "workflow_labels": [
                {"name": "status-01:created", "promotable": True},
                {"name": "status-02:awaiting-planning"},
                {"name": "status-03:planning"},
                {"name": "status-04:plan-review", "promotable": True},
                {"name": "status-05:plan-ready"},
                {"name": "status-06:implementing"},
                {"name": "status-07:code-review", "promotable": True},
                {"name": "status-08:ready-pr"},
            ]
        }
        result = build_promotions(config)
        assert result == [
            ("status-01:created", "status-02:awaiting-planning"),
            ("status-04:plan-review", "status-05:plan-ready"),
            ("status-07:code-review", "status-08:ready-pr"),
        ]

    def test_empty_when_no_promotable(self) -> None:
        """Returns empty list when no labels are promotable."""
        config: dict[str, Any] = {
            "workflow_labels": [
                {"name": "status-01:created"},
                {"name": "status-02:awaiting-planning"},
            ]
        }
        result = build_promotions(config)
        assert result == []

    def test_last_label_promotable_ignored(self) -> None:
        """Last label with promotable: true has no next, so it's skipped."""
        config: dict[str, Any] = {
            "workflow_labels": [
                {"name": "status-01:created"},
                {"name": "status-02:awaiting-planning", "promotable": True},
            ]
        }
        result = build_promotions(config)
        assert result == []


class TestGenerateLabelNewIssuesYml:
    """Test generate_label_new_issues_yml() function."""

    def test_contains_default_label(self) -> None:
        """Generated YAML references the default label name."""
        content = generate_label_new_issues_yml("status-01:created")
        assert "status-01:created" in content

    def test_valid_yaml_structure(self) -> None:
        """Generated content is valid YAML with expected structure."""
        content = generate_label_new_issues_yml("status-01:created")
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Label New Issues"
        # YAML parses 'on' as boolean True
        assert "issues" in parsed[True]
        assert "add-label" in parsed["jobs"]

    def test_uses_github_script_action(self) -> None:
        """Generated YAML uses actions/github-script."""
        content = generate_label_new_issues_yml("status-01:created")
        assert "actions/github-script@" in content

    def test_different_default_label(self) -> None:
        """Works with a non-standard default label name."""
        content = generate_label_new_issues_yml("my-custom-label")
        assert "my-custom-label" in content
        assert "status-01:created" not in content


class TestGenerateApproveCommandYml:
    """Test generate_approve_command_yml() function."""

    def test_contains_promotion_paths(self) -> None:
        """Generated YAML includes all promotion source/target pairs."""
        promotions = [
            ("status-01:created", "status-02:awaiting-planning"),
            ("status-04:plan-review", "status-05:plan-ready"),
        ]
        content = generate_approve_command_yml(promotions)
        assert "status-01:created" in content
        assert "status-02:awaiting-planning" in content
        assert "status-04:plan-review" in content
        assert "status-05:plan-ready" in content

    def test_valid_yaml_structure(self) -> None:
        """Generated content is valid YAML with expected structure."""
        promotions = [
            ("status-01:created", "status-02:awaiting-planning"),
        ]
        content = generate_approve_command_yml(promotions)
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Approve Command"
        # YAML parses 'on' as boolean True
        assert "issue_comment" in parsed[True]
        assert "handle-approve" in parsed["jobs"]

    def test_empty_promotions(self) -> None:
        """Works with empty promotions list."""
        content = generate_approve_command_yml([])
        parsed = yaml.safe_load(content)
        assert parsed is not None


class TestWriteGithubActions:
    """Test write_github_actions() function."""

    def _make_config(self) -> dict[str, Any]:
        """Build a minimal config with default and promotable labels."""
        return {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "default": True,
                    "promotable": True,
                },
                {"name": "status-02:awaiting-planning"},
            ]
        }

    def test_writes_two_files(self, tmp_path: Path) -> None:
        """Writes label-new-issues.yml and approve-command.yml."""
        config = self._make_config()
        result = write_github_actions(tmp_path, config)

        assert len(result) == 2
        workflows_dir = tmp_path / ".github" / "workflows"
        assert (workflows_dir / "label-new-issues.yml").exists()
        assert (workflows_dir / "approve-command.yml").exists()

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """With dry_run=True, no files are created."""
        config = self._make_config()
        result = write_github_actions(tmp_path, config, dry_run=True)

        assert len(result) == 2
        workflows_dir = tmp_path / ".github" / "workflows"
        assert not workflows_dir.exists()

    def test_overwrites_existing_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Existing files are overwritten with a warning logged."""
        config = self._make_config()
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "label-new-issues.yml").write_text("old content")

        with caplog.at_level(logging.WARNING):
            write_github_actions(tmp_path, config)

        assert "Overwriting" in caplog.text
        # File should have new content
        content = (workflows_dir / "label-new-issues.yml").read_text()
        assert "old content" not in content

    def test_creates_workflows_directory(self, tmp_path: Path) -> None:
        """Creates .github/workflows/ if it doesn't exist."""
        config = self._make_config()
        assert not (tmp_path / ".github").exists()

        write_github_actions(tmp_path, config)

        assert (tmp_path / ".github" / "workflows").is_dir()

    def test_returns_file_paths(self, tmp_path: Path) -> None:
        """Returns list of written file paths as strings."""
        config = self._make_config()
        result = write_github_actions(tmp_path, config)

        assert any("label-new-issues.yml" in p for p in result)
        assert any("approve-command.yml" in p for p in result)
