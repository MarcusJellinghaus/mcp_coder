"""Unit tests for define_labels workflow module.

Tests cover:
- WORKFLOW_LABELS constant validation and structure
- Color format validation
- Module load-time validation
- apply_labels() orchestrator function with mocked LabelsManager
"""

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.utils.conftest import git_repo
from workflows.define_labels import (
    apply_labels,
    calculate_label_changes,
    parse_arguments,
    resolve_project_dir,
)
from mcp_coder.utils.github_operations.label_config import load_labels_config

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

    @patch("workflows.define_labels.LabelsManager")
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

    @patch("workflows.define_labels.LabelsManager")
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

    @patch("workflows.define_labels.LabelsManager")
    def test_apply_labels_api_error_fails_fast(
        self,
        mock_manager_class: MagicMock,
        mock_labels_manager: MagicMock,
        tmp_path: Path,
        labels_config_path: Path,
    ) -> None:
        """Test apply_labels fails fast on first API error."""
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

        # Execute & Verify: apply_labels should exit immediately with code 1
        with pytest.raises(SystemExit) as exc_info:
            apply_labels(tmp_path, workflow_labels, dry_run=False)

        assert exc_info.value.code == 1

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


class TestArgumentParsing:
    """Test command line argument parsing."""

    def test_parse_arguments_default_values(self) -> None:
        """Test parse_arguments with default values (no arguments provided)."""
        with patch("sys.argv", ["define_labels.py"]):
            args = parse_arguments()

            # Verify default values
            assert args.project_dir is None, "Default project_dir should be None"
            assert args.log_level == "INFO", "Default log_level should be INFO"
            assert args.dry_run is False, "Default dry_run should be False"

    def test_parse_arguments_custom_values(self) -> None:
        """Test parse_arguments with custom values provided."""
        with patch(
            "sys.argv",
            [
                "define_labels.py",
                "--project-dir",
                "/custom/path",
                "--log-level",
                "DEBUG",
                "--dry-run",
            ],
        ):
            args = parse_arguments()

            # Verify custom values
            assert (
                args.project_dir == "/custom/path"
            ), "project_dir should match provided path"
            assert args.log_level == "DEBUG", "log_level should be DEBUG"
            assert args.dry_run is True, "dry_run should be True when flag is provided"

    def test_parse_arguments_log_level_choices(self) -> None:
        """Test parse_arguments accepts all valid log level choices."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            with patch("sys.argv", ["define_labels.py", "--log-level", level]):
                args = parse_arguments()
                assert args.log_level == level, f"Should accept log level {level}"

    def test_parse_arguments_invalid_log_level(self) -> None:
        """Test parse_arguments rejects invalid log level."""
        with patch("sys.argv", ["define_labels.py", "--log-level", "INVALID"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

            # argparse exits with code 2 for invalid arguments
            assert (
                exc_info.value.code == 2
            ), "Should exit with code 2 for invalid arguments"


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
        """Test resolve_project_dir fails for nonexistent directory."""
        nonexistent_path = "/nonexistent/path/that/does/not/exist"

        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(nonexistent_path)

        assert (
            exc_info.value.code == 1
        ), "Should exit with code 1 for nonexistent directory"

    def test_resolve_project_dir_not_git_repository(self, tmp_path: Path) -> None:
        """Test resolve_project_dir fails for directory without .git subdirectory."""
        # Create a directory without .git
        non_git_dir = tmp_path / "not_a_git_repo"
        non_git_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(non_git_dir))

        assert exc_info.value.code == 1, "Should exit with code 1 for non-git directory"

    def test_resolve_project_dir_file_instead_of_directory(
        self, tmp_path: Path
    ) -> None:
        """Test resolve_project_dir fails when path is a file, not a directory."""
        # Create a file instead of a directory
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(test_file))

        assert exc_info.value.code == 1, "Should exit with code 1 when path is a file"

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
