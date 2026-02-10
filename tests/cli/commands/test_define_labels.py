"""Unit tests for define_labels CLI command module.

Tests cover:
- WORKFLOW_LABELS constant validation and structure
- Color format validation
- Module load-time validation
- apply_labels() orchestrator function with mocked LabelsManager
- execute_define_labels() CLI command function
"""

import argparse
import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.define_labels import (
    apply_labels,
    calculate_label_changes,
    check_status_labels,
    execute_define_labels,
    initialize_issues,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.github_operations.label_config import load_labels_config
from mcp_coder.workflows.utils import resolve_project_dir
from tests.utils.conftest import git_repo

# Note: labels_config_path fixture is defined in conftest.py


class TestWorkflowLabelsFromConfig:
    """Test loading workflow labels from JSON config."""

    def test_load_workflow_labels_from_json(
        self, tmp_path: Path, labels_config_path: Path
    ) -> None:
        """Test that workflow labels can be loaded from JSON config."""
        # Create a temporary config file
        config_dir = tmp_path / "workflows" / "config"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "labels.json"

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


class TestCalculateLabelChanges:
    """Test the calculate_label_changes pure function."""

    def test_calculate_label_changes_empty_repo(self) -> None:
        """Test calculate_label_changes with empty repository (no existing labels)."""
        existing_labels: list[tuple[str, str, str]] = []
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-02:awaiting-planning", "6ee7b7", "Ready for planning"),
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # All target labels should be created
        assert result["created"] == [
            "status-01:created",
            "status-02:awaiting-planning",
        ]
        assert result["updated"] == []
        assert result["deleted"] == []
        assert result["unchanged"] == []

    def test_calculate_label_changes_creates_new_labels(self) -> None:
        """Test that new labels are identified for creation."""
        existing_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
        ]
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-02:awaiting-planning", "6ee7b7", "Ready for planning"),
            ("status-03:planning", "a7f3d0", "Planning in progress"),
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # Two new labels should be created
        assert result["created"] == [
            "status-02:awaiting-planning",
            "status-03:planning",
        ]
        # First label unchanged
        assert result["unchanged"] == ["status-01:created"]
        assert result["updated"] == []
        assert result["deleted"] == []

    def test_calculate_label_changes_updates_existing_labels(self) -> None:
        """Test that labels needing updates are identified correctly."""
        existing_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-02:awaiting-planning", "OLDCOL", "Old description"),
            ("status-03:planning", "a7f3d0", "Planning in progress"),
        ]
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),  # unchanged
            (
                "status-02:awaiting-planning",
                "6ee7b7",
                "Ready for planning",
            ),  # color changed
            (
                "status-03:planning",
                "a7f3d0",
                "Updated description",
            ),  # description changed
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # Two labels need updates
        assert result["updated"] == [
            "status-02:awaiting-planning",
            "status-03:planning",
        ]
        assert result["unchanged"] == ["status-01:created"]
        assert result["created"] == []
        assert result["deleted"] == []

    def test_calculate_label_changes_deletes_obsolete_status_labels(self) -> None:
        """Test that obsolete status-* labels are identified for deletion."""
        existing_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-99:obsolete", "AABBCC", "Old label to remove"),
            ("status-98:deprecated", "DDEEFF", "Another old label"),
        ]
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # Two obsolete status labels should be deleted
        assert set(result["deleted"]) == {"status-99:obsolete", "status-98:deprecated"}
        assert result["unchanged"] == ["status-01:created"]
        assert result["created"] == []
        assert result["updated"] == []

    def test_calculate_label_changes_skips_unchanged_labels(self) -> None:
        """Test that unchanged labels are correctly identified."""
        existing_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-02:awaiting-planning", "6ee7b7", "Ready for planning"),
            ("status-03:planning", "a7f3d0", "Planning in progress"),
        ]
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-02:awaiting-planning", "6ee7b7", "Ready for planning"),
            ("status-03:planning", "a7f3d0", "Planning in progress"),
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # All labels unchanged
        assert result["unchanged"] == [
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        ]
        assert result["created"] == []
        assert result["updated"] == []
        assert result["deleted"] == []


class TestApplyLabels:
    """Test the apply_labels orchestrator function with mocked LabelsManager."""

    @pytest.fixture
    def mock_labels_manager(self) -> MagicMock:
        """Create a mock LabelsManager for testing.

        Returns:
            MagicMock configured to simulate LabelsManager behavior
        """
        mock = MagicMock()

        # Configure mock to return empty list by default
        mock.get_labels.return_value = []

        # Configure mock to return success for create/update/delete
        mock.create_label.return_value = {
            "name": "test-label",
            "color": "10b981",
            "description": "Test description",
            "url": "https://api.github.com/repos/test/test/labels/test-label",
        }
        mock.update_label.return_value = {
            "name": "test-label",
            "color": "10b981",
            "description": "Updated description",
            "url": "https://api.github.com/repos/test/test/labels/test-label",
        }
        mock.delete_label.return_value = True

        return mock

    @patch("mcp_coder.cli.commands.define_labels.LabelsManager")
    def test_apply_labels_success_flow(
        self,
        mock_manager_class: MagicMock,
        mock_labels_manager: MagicMock,
        tmp_path: Path,
        labels_config_path: Path,
    ) -> None:
        """Test apply_labels success flow with create, update, delete operations."""
        # Setup: Configure mock to return existing labels
        existing_labels_data = [
            {
                "name": "status-01:created",
                "color": "OLDCOL",
                "description": "Old description",
            },  # needs update
            {
                "name": "status-99:obsolete",
                "color": "ABCDEF",
                "description": "To be deleted",
            },  # needs delete
        ]
        mock_labels_manager.get_labels.return_value = existing_labels_data
        mock_manager_class.return_value = mock_labels_manager

        # Load workflow labels from config
        labels_config = load_labels_config(labels_config_path)
        workflow_labels = [
            (label["name"], label["color"], label["description"])
            for label in labels_config["workflow_labels"]
        ]

        # Execute: Call apply_labels with dry_run=False
        result = apply_labels(tmp_path, workflow_labels, dry_run=False)

        # Verify: LabelsManager was initialized with project_dir
        mock_manager_class.assert_called_once_with(tmp_path)

        # Verify: get_labels was called
        mock_labels_manager.get_labels.assert_called_once()

        # Verify: Result contains expected changes
        assert "status-01:created" in result["updated"]
        assert "status-99:obsolete" in result["deleted"]
        assert len(result["created"]) == 9  # 9 new labels (10 total - 1 existing)

        # Verify: API methods were called for changes
        assert mock_labels_manager.create_label.call_count == 9
        assert mock_labels_manager.update_label.call_count == 1
        assert mock_labels_manager.delete_label.call_count == 1

        # Verify: update_label was called with correct parameters
        mock_labels_manager.update_label.assert_called_once_with(
            "status-01:created",
            color="10b981",
            description="Fresh issue, may need refinement",
        )

        # Verify: delete_label was called with correct parameters
        mock_labels_manager.delete_label.assert_called_once_with("status-99:obsolete")

    @patch("mcp_coder.cli.commands.define_labels.LabelsManager")
    def test_apply_labels_dry_run_mode(
        self,
        mock_manager_class: MagicMock,
        mock_labels_manager: MagicMock,
        tmp_path: Path,
        labels_config_path: Path,
    ) -> None:
        """Test apply_labels dry-run mode does not make API calls."""
        # Setup: Configure mock to return existing labels needing changes
        existing_labels_data = [
            {
                "name": "status-01:created",
                "color": "OLDCOL",
                "description": "Old description",
            },  # needs update
            {
                "name": "status-99:obsolete",
                "color": "ABCDEF",
                "description": "To be deleted",
            },  # needs delete
        ]
        mock_labels_manager.get_labels.return_value = existing_labels_data
        mock_manager_class.return_value = mock_labels_manager

        # Load workflow labels from config
        labels_config = load_labels_config(labels_config_path)
        workflow_labels = [
            (label["name"], label["color"], label["description"])
            for label in labels_config["workflow_labels"]
        ]

        # Execute: Call apply_labels with dry_run=True
        result = apply_labels(tmp_path, workflow_labels, dry_run=True)

        # Verify: get_labels was called (read operation is OK in dry-run)
        mock_labels_manager.get_labels.assert_called_once()

        # Verify: Result contains expected changes
        assert "status-01:created" in result["updated"]
        assert "status-99:obsolete" in result["deleted"]
        assert len(result["created"]) == 9

        # Verify: NO API write methods were called in dry-run mode
        mock_labels_manager.create_label.assert_not_called()
        mock_labels_manager.update_label.assert_not_called()
        mock_labels_manager.delete_label.assert_not_called()

    @patch("mcp_coder.cli.commands.define_labels.LabelsManager")
    def test_apply_labels_api_error_raises_runtime_error(
        self,
        mock_manager_class: MagicMock,
        mock_labels_manager: MagicMock,
        tmp_path: Path,
        labels_config_path: Path,
    ) -> None:
        """Test apply_labels raises RuntimeError on API error."""
        # Setup: Configure mock to return empty labels (all need creation)
        mock_labels_manager.get_labels.return_value = []

        # Configure mock to raise exception on first create_label call
        mock_labels_manager.create_label.side_effect = Exception(
            "GitHub API error: rate limit exceeded"
        )

        mock_manager_class.return_value = mock_labels_manager

        # Load workflow labels from config
        labels_config = load_labels_config(labels_config_path)
        workflow_labels = [
            (label["name"], label["color"], label["description"])
            for label in labels_config["workflow_labels"]
        ]

        # Execute & Verify: apply_labels should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to create label"):
            apply_labels(tmp_path, workflow_labels, dry_run=False)

        # Verify: create_label was called only once (failed fast)
        assert mock_labels_manager.create_label.call_count == 1

        # Verify: No other API methods were called after the error
        mock_labels_manager.update_label.assert_not_called()
        mock_labels_manager.delete_label.assert_not_called()

    def test_calculate_label_changes_preserves_non_status_labels(self) -> None:
        """Test that non-status-* labels are preserved (not deleted)."""
        existing_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("bug", "FF0000", "Bug report"),
            ("enhancement", "00FF00", "Feature request"),
            ("documentation", "0000FF", "Documentation update"),
        ]
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # Non-status labels should NOT be deleted
        assert result["deleted"] == []
        assert result["unchanged"] == ["status-01:created"]
        assert result["created"] == []
        assert result["updated"] == []

    def test_calculate_label_changes_partial_match(self) -> None:
        """Test with partial match: 5 of 10 labels exist, some need updates."""
        existing_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            (
                "status-02:awaiting-planning",
                "OLDCOL",
                "Old description",
            ),  # needs update
            ("status-03:planning", "a7f3d0", "Planning in progress"),
            ("status-04:plan-review", "3b82f6", "Plan ready for review"),
            ("status-05:plan-ready", "93c5fd", "Plan approved"),
            ("status-99:obsolete", "ABCDEF", "To be deleted"),  # obsolete
        ]
        target_labels = [
            ("status-01:created", "10b981", "Fresh issue"),
            ("status-02:awaiting-planning", "6ee7b7", "Updated description"),
            ("status-03:planning", "a7f3d0", "Planning in progress"),
            ("status-04:plan-review", "3b82f6", "Plan ready for review"),
            ("status-05:plan-ready", "93c5fd", "Plan approved"),
            ("status-06:implementing", "bfdbfe", "Code being written"),  # new
            ("status-07:code-review", "f59e0b", "Needs code review"),  # new
            ("status-08:ready-pr", "fbbf24", "Ready for PR"),  # new
            ("status-09:pr-creating", "fed7aa", "Creating PR"),  # new
            ("status-10:pr-created", "8b5cf6", "PR created"),  # new
        ]

        result = calculate_label_changes(existing_labels, target_labels)

        # Verify correct categorization
        assert result["created"] == [
            "status-06:implementing",
            "status-07:code-review",
            "status-08:ready-pr",
            "status-09:pr-creating",
            "status-10:pr-created",
        ]
        assert result["updated"] == ["status-02:awaiting-planning"]
        assert result["deleted"] == ["status-99:obsolete"]
        assert result["unchanged"] == [
            "status-01:created",
            "status-03:planning",
            "status-04:plan-review",
            "status-05:plan-ready",
        ]

    def test_calculate_label_changes_all_exist_unchanged(
        self, labels_config_path: Path
    ) -> None:
        """Test when all 10 workflow labels already exist with correct values."""
        # Load workflow labels from config
        labels_config = load_labels_config(labels_config_path)
        workflow_labels = [
            (label["name"], label["color"], label["description"])
            for label in labels_config["workflow_labels"]
        ]

        # Use actual workflow_labels as both existing and target
        existing_labels = list(workflow_labels)
        target_labels = list(workflow_labels)

        result = calculate_label_changes(existing_labels, target_labels)

        # All should be unchanged
        expected_names = [label[0] for label in workflow_labels]
        assert result["unchanged"] == expected_names
        assert result["created"] == []
        assert result["updated"] == []
        assert result["deleted"] == []


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
                {"name": "status-01:created", "color": "10b981", "description": "Test"}
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

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


class TestStaleTimeoutConfiguration:
    """Test stale_timeout_minutes field in labels configuration."""

    def test_bot_busy_labels_have_stale_timeout(self, labels_config_path: Path) -> None:
        """Test that all bot_busy labels have stale_timeout_minutes field."""
        labels_config = load_labels_config(labels_config_path)

        bot_busy_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label.get("category") == "bot_busy"
        ]

        # Ensure we have bot_busy labels to test
        assert len(bot_busy_labels) > 0, "Should have at least one bot_busy label"

        for label in bot_busy_labels:
            assert (
                "stale_timeout_minutes" in label
            ), f"bot_busy label '{label['name']}' should have stale_timeout_minutes field"

    def test_stale_timeout_values_are_positive_integers(
        self, labels_config_path: Path
    ) -> None:
        """Test that stale_timeout_minutes values are positive integers."""
        labels_config = load_labels_config(labels_config_path)

        bot_busy_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label.get("category") == "bot_busy"
        ]

        for label in bot_busy_labels:
            timeout = label.get("stale_timeout_minutes")
            assert isinstance(
                timeout, int
            ), f"stale_timeout_minutes for '{label['name']}' should be an integer"
            assert (
                timeout > 0
            ), f"stale_timeout_minutes for '{label['name']}' should be positive"

    def test_expected_timeout_values(self, labels_config_path: Path) -> None:
        """Test specific timeout values match requirements."""
        labels_config = load_labels_config(labels_config_path)

        # Build lookup by internal_id
        labels_by_id = {
            label["internal_id"]: label for label in labels_config["workflow_labels"]
        }

        # Expected timeout values per spec
        expected_timeouts = {
            "planning": 15,
            "implementing": 120,
            "pr_creating": 15,
        }

        for internal_id, expected_timeout in expected_timeouts.items():
            assert (
                internal_id in labels_by_id
            ), f"Label with internal_id '{internal_id}' should exist"
            label = labels_by_id[internal_id]
            actual_timeout = label.get("stale_timeout_minutes")
            assert actual_timeout == expected_timeout, (
                f"stale_timeout_minutes for '{internal_id}' should be {expected_timeout}, "
                f"got {actual_timeout}"
            )


class TestCheckStatusLabels:
    """Test check_status_labels function."""

    def test_no_status_labels_returns_zero(self) -> None:
        """Test that issues without status labels return count of 0."""
        issue: IssueData = {
            "number": 1,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["bug", "enhancement"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 0
        assert found_labels == []

    def test_single_status_label_returns_one(self) -> None:
        """Test that issues with one status label return count of 1."""
        issue: IssueData = {
            "number": 2,
            "title": "Test issue with label",
            "body": "",
            "state": "open",
            "labels": ["bug", "status-01:created", "enhancement"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 1
        assert found_labels == ["status-01:created"]

    def test_multiple_status_labels_returns_count(self) -> None:
        """Test that issues with multiple status labels return correct count."""
        issue: IssueData = {
            "number": 3,
            "title": "Test issue with multiple labels",
            "body": "",
            "state": "open",
            "labels": ["status-01:created", "status-02:awaiting-planning"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 2
        assert set(found_labels) == {"status-01:created", "status-02:awaiting-planning"}

    def test_ignores_non_workflow_labels(self) -> None:
        """Test that non-workflow labels are ignored in the count."""
        issue: IssueData = {
            "number": 4,
            "title": "Test issue with mixed labels",
            "body": "",
            "state": "open",
            "labels": [
                "bug",
                "status-01:created",
                "enhancement",
                "priority-high",
                "documentation",
            ],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 1
        assert found_labels == ["status-01:created"]


class TestInitializeIssues:
    """Test initialize_issues function."""

    def test_initializes_issues_without_labels(self) -> None:
        """Test that issues without status labels are initialized."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Issue without labels",
                "body": "",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Another issue without labels",
                "body": "",
                "state": "open",
                "labels": [],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created", "status-02:awaiting-planning"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()
        mock_issue_manager.add_labels.return_value = {
            "number": 1,
            "labels": ["status-01:created"],
        }

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=False,
        )

        assert result == [1, 2]
        assert mock_issue_manager.add_labels.call_count == 2
        mock_issue_manager.add_labels.assert_any_call(1, "status-01:created")
        mock_issue_manager.add_labels.assert_any_call(2, "status-01:created")

    def test_skips_issues_with_labels(self) -> None:
        """Test that issues with status labels are skipped."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Issue with status label",
                "body": "",
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue without labels",
                "body": "",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created", "status-02:awaiting-planning"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()
        mock_issue_manager.add_labels.return_value = {"number": 2, "labels": []}

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=False,
        )

        # Only issue 2 should be initialized
        assert result == [2]
        assert mock_issue_manager.add_labels.call_count == 1
        mock_issue_manager.add_labels.assert_called_once_with(2, "status-01:created")

    def test_dry_run_does_not_call_api(self) -> None:
        """Test that dry-run mode does not call the API."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Issue without labels",
                "body": "",
                "state": "open",
                "labels": [],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=True,
        )

        # Issue should be in result but API should NOT be called
        assert result == [1]
        mock_issue_manager.add_labels.assert_not_called()

    def test_returns_initialized_issue_numbers(self) -> None:
        """Test that the function returns the correct list of issue numbers."""
        issues: list[IssueData] = [
            {
                "number": 10,
                "title": "Issue 10",
                "body": "",
                "state": "open",
                "labels": [],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 20,
                "title": "Issue 20",
                "body": "",
                "state": "open",
                "labels": ["status-01:created"],  # Has label, skip
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 30,
                "title": "Issue 30",
                "body": "",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created", "status-02:awaiting-planning"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()
        mock_issue_manager.add_labels.return_value = {"number": 0, "labels": []}

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=False,
        )

        # Only issues 10 and 30 should be initialized (20 already has a label)
        assert result == [10, 30]
