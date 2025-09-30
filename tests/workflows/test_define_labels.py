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

from workflows.define_labels import (
    WORKFLOW_LABELS,
    _validate_color_format,
    _validate_workflow_labels,
    apply_labels,
    calculate_label_changes,
)


class TestWorkflowLabelsConstant:
    """Test the WORKFLOW_LABELS constant definition and validation."""

    def test_workflow_labels_constant(self) -> None:
        """Test WORKFLOW_LABELS constant has correct structure and all 10 status labels."""
        # Verify we have exactly 10 labels
        assert (
            len(WORKFLOW_LABELS) == 10
        ), "WORKFLOW_LABELS should contain exactly 10 status labels"

        # Verify each label has correct structure: (name, color, description)
        for i, label in enumerate(WORKFLOW_LABELS, start=1):
            assert isinstance(label, tuple), f"Label {i} should be a tuple"
            assert (
                len(label) == 3
            ), f"Label {i} should have 3 elements (name, color, description)"

            name, color, description = label

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

    def test_workflow_labels_sequence(self) -> None:
        """Test that workflow labels follow correct sequential numbering."""
        expected_numbers = [f"{i:02d}" for i in range(1, 11)]

        for i, label in enumerate(WORKFLOW_LABELS):
            name = label[0]
            expected_prefix = f"status-{expected_numbers[i]}:"
            assert name.startswith(
                expected_prefix
            ), f"Label {i+1} should start with '{expected_prefix}'"

    def test_workflow_labels_names(self) -> None:
        """Test that all expected workflow label names are present."""
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

        actual_names = [label[0] for label in WORKFLOW_LABELS]
        assert (
            actual_names == expected_names
        ), "Workflow label names should match expected sequence"

    def test_workflow_labels_unique_names(self) -> None:
        """Test that all workflow label names are unique."""
        names = [label[0] for label in WORKFLOW_LABELS]
        assert len(names) == len(
            set(names)
        ), "All workflow label names should be unique"

    def test_workflow_labels_unique_colors(self) -> None:
        """Test that all workflow label colors are unique."""
        colors = [label[1] for label in WORKFLOW_LABELS]
        assert len(colors) == len(
            set(colors)
        ), "All workflow label colors should be unique"

    def test_workflow_labels_immutability(self) -> None:
        """Test that WORKFLOW_LABELS is a list of tuples (immutable entries)."""
        assert isinstance(WORKFLOW_LABELS, list), "WORKFLOW_LABELS should be a list"

        for label in WORKFLOW_LABELS:
            assert isinstance(label, tuple), "Each label should be an immutable tuple"


class TestColorFormatValidation:
    """Test color format validation function."""

    def test_validate_color_format_valid(self) -> None:
        """Test _validate_color_format with valid hex colors."""
        valid_colors = [
            "10b981",
            "6ee7b7",
            "a7f3d0",
            "3b82f6",
            "93c5fd",
            "bfdbfe",
            "f59e0b",
            "fbbf24",
            "fed7aa",
            "8b5cf6",
            "AABBCC",  # uppercase
            "aAbBcC",  # mixed case
            "123456",
            "000000",
            "FFFFFF",
        ]

        for color in valid_colors:
            assert _validate_color_format(color), f"'{color}' should be valid hex color"

    def test_validate_color_format_invalid(self) -> None:
        """Test _validate_color_format with invalid formats."""
        invalid_colors = [
            "#10b981",  # has '#' prefix
            "10b98",  # too short
            "10b9811",  # too long
            "gggggg",  # invalid hex chars
            "10b 981",  # contains space
            "",  # empty string
            "10b-981",  # contains dash
        ]

        for color in invalid_colors:
            assert not _validate_color_format(color), f"'{color}' should be invalid"

    def test_validate_color_format_non_string(self) -> None:
        """Test _validate_color_format with non-string inputs."""
        invalid_inputs: list[Any] = [
            None,
            123456,
            ["10b981"],
            {"color": "10b981"},
        ]

        for invalid_input in invalid_inputs:
            assert not _validate_color_format(
                invalid_input
            ), f"{invalid_input} should be invalid"


class TestWorkflowLabelsModuleValidation:
    """Test module load-time validation of WORKFLOW_LABELS."""

    def test_validate_workflow_labels_success(self) -> None:
        """Test that _validate_workflow_labels succeeds with current WORKFLOW_LABELS."""
        # Should not raise any exceptions
        try:
            _validate_workflow_labels()
        except Exception as e:
            pytest.fail(f"_validate_workflow_labels() raised unexpected exception: {e}")

    def test_validate_workflow_labels_with_mock_data(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation behavior with various invalid label structures."""
        import workflows.define_labels as define_labels_module

        # Test invalid structure: not a tuple
        invalid_labels = [["status-01:test", "10b981", "description"]]
        monkeypatch.setattr(define_labels_module, "WORKFLOW_LABELS", invalid_labels)

        with pytest.raises(ValueError, match="Invalid label structure"):
            _validate_workflow_labels()

    def test_validate_workflow_labels_invalid_tuple_length(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation fails with wrong tuple length."""
        import workflows.define_labels as define_labels_module

        # Test tuple with wrong number of elements
        invalid_labels = [("status-01:test", "10b981")]  # missing description
        monkeypatch.setattr(define_labels_module, "WORKFLOW_LABELS", invalid_labels)

        with pytest.raises(ValueError, match="Invalid label structure"):
            _validate_workflow_labels()

    def test_validate_workflow_labels_invalid_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation fails with invalid label name."""
        import workflows.define_labels as define_labels_module

        # Test empty name
        invalid_labels = [("", "10b981", "description")]
        monkeypatch.setattr(define_labels_module, "WORKFLOW_LABELS", invalid_labels)

        with pytest.raises(ValueError, match="Invalid label name"):
            _validate_workflow_labels()

        # Test non-string name
        invalid_labels_non_string: list[Any] = [(123, "10b981", "description")]
        monkeypatch.setattr(
            define_labels_module, "WORKFLOW_LABELS", invalid_labels_non_string
        )

        with pytest.raises(ValueError, match="Invalid label name"):
            _validate_workflow_labels()

    def test_validate_workflow_labels_invalid_color(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation fails with invalid color format."""
        import workflows.define_labels as define_labels_module

        # Test invalid hex color
        invalid_labels = [("status-01:test", "#10b981", "description")]
        monkeypatch.setattr(define_labels_module, "WORKFLOW_LABELS", invalid_labels)

        with pytest.raises(ValueError, match="Invalid color format"):
            _validate_workflow_labels()

        # Test too short
        invalid_labels = [("status-01:test", "10b98", "description")]
        monkeypatch.setattr(define_labels_module, "WORKFLOW_LABELS", invalid_labels)

        with pytest.raises(ValueError, match="Invalid color format"):
            _validate_workflow_labels()

    def test_validate_workflow_labels_invalid_description(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation fails with invalid description."""
        import workflows.define_labels as define_labels_module

        # Test non-string description
        invalid_labels = [("status-01:test", "10b981", 123)]
        monkeypatch.setattr(define_labels_module, "WORKFLOW_LABELS", invalid_labels)

        with pytest.raises(ValueError, match="Invalid description"):
            _validate_workflow_labels()


class TestWorkflowLabelsContent:
    """Test specific content and metadata of workflow labels."""

    def test_all_labels_have_descriptions(self) -> None:
        """Test that all labels have non-empty descriptions."""
        for label in WORKFLOW_LABELS:
            description = label[2]
            assert (
                description.strip()
            ), f"Label '{label[0]}' should have non-empty description"

    def test_status_labels_cover_workflow_stages(self) -> None:
        """Test that labels cover the expected workflow stages."""
        # Check for key workflow stages
        names = [label[0] for label in WORKFLOW_LABELS]

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

    def test_color_codes_are_github_compatible(self) -> None:
        """Test that all color codes follow GitHub API format (6-char hex without #)."""
        for label in WORKFLOW_LABELS:
            name, color, _ = label

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

        # Execute: Call apply_labels with dry_run=False
        result = apply_labels(tmp_path, dry_run=False)

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

        # Execute: Call apply_labels with dry_run=True
        result = apply_labels(tmp_path, dry_run=True)

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
    ) -> None:
        """Test apply_labels fails fast on first API error."""
        # Setup: Configure mock to return empty labels (all need creation)
        mock_labels_manager.get_labels.return_value = []

        # Configure mock to raise exception on first create_label call
        mock_labels_manager.create_label.side_effect = Exception(
            "GitHub API error: rate limit exceeded"
        )

        mock_manager_class.return_value = mock_labels_manager

        # Execute & Verify: apply_labels should exit immediately with code 1
        with pytest.raises(SystemExit) as exc_info:
            apply_labels(tmp_path, dry_run=False)

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

    def test_calculate_label_changes_all_exist_unchanged(self) -> None:
        """Test when all 10 workflow labels already exist with correct values."""
        # Use actual WORKFLOW_LABELS as both existing and target
        existing_labels = list(WORKFLOW_LABELS)
        target_labels = list(WORKFLOW_LABELS)

        result = calculate_label_changes(existing_labels, target_labels)

        # All should be unchanged
        expected_names = [label[0] for label in WORKFLOW_LABELS]
        assert result["unchanged"] == expected_names
        assert result["created"] == []
        assert result["updated"] == []
        assert result["deleted"] == []
