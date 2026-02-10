"""Unit tests for define_labels label change calculations.

Tests cover:
- calculate_label_changes pure function
- apply_labels orchestrator function with mocked LabelsManager
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.define_labels import (
    apply_labels,
    calculate_label_changes,
)
from mcp_coder.utils.github_operations.label_config import load_labels_config


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
