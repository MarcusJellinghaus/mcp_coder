"""Tests for define_labels validation summary formatting.

Tests cover:
- Validation summary formatting (format_validation_summary function)
"""

from mcp_coder.cli.commands.define_labels import (
    ValidationResults,
    format_validation_summary,
)


class TestFormatValidationSummary:
    """Test format_validation_summary function."""

    def test_includes_label_sync_counts(self) -> None:
        """Test that summary includes label sync counts."""
        label_changes = {
            "created": ["status-01:created", "status-02:awaiting-planning"],
            "updated": ["status-03:planning"],
            "deleted": [],
            "unchanged": [
                "status-04:plan-review",
                "status-05:plan-ready",
                "status-06:implementing",
            ],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=True,
            gen_actions_requested=False,
        )

        assert "Created=2" in result
        assert "Updated=1" in result
        assert "Deleted=0" in result
        assert "Unchanged=3" in result

    def test_includes_initialized_issues(self) -> None:
        """Test that summary includes initialized issue count."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [12, 45, 78],
            "errors": [],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=True,
            gen_actions_requested=False,
        )

        assert "Issues initialized: 3" in result

    def test_includes_error_details(self) -> None:
        """Test that summary includes error details with issue numbers and labels."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [
                {
                    "issue": 45,
                    "labels": ["status-01:created", "status-03:planning"],
                }
            ],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=True,
            gen_actions_requested=False,
        )

        assert "Errors (multiple status labels): 1" in result
        assert "#45" in result
        assert "status-01:created" in result
        assert "status-03:planning" in result

    def test_includes_warning_with_threshold(self) -> None:
        """Test that summary includes warning details with elapsed and threshold."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [
                {
                    "issue": 78,
                    "label": "status-06:implementing",
                    "elapsed": 150,
                    "threshold": 120,
                }
            ],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=True,
            gen_actions_requested=False,
        )

        assert "Warnings (stale bot processes): 1" in result
        assert "#78" in result
        assert "status-06:implementing" in result
        assert "150 minutes" in result
        assert "threshold: 120" in result

    def test_no_errors_or_warnings_shows_clean_summary(self) -> None:
        """Test that clean summary shows success when no errors or warnings."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=True,
            gen_actions_requested=False,
        )

        # Should not contain error or warning sections
        assert "Errors" not in result
        assert "Warnings" not in result

    def test_init_skipped_shows_skipped(self) -> None:
        """When init_requested=False, summary shows 'skipped' for initialized."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=False,
            validate_requested=True,
            gen_actions_requested=False,
        )

        assert "Issues initialized: skipped" in result

    def test_validate_skipped_shows_skipped(self) -> None:
        """When validate_requested=False, summary omits error/warning sections."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=False,
            gen_actions_requested=False,
        )

        # Should not contain error or warning sections when validate not requested
        assert "Errors" not in result
        assert "Warnings" not in result

    def test_both_requested_shows_counts(self) -> None:
        """When both requested, summary shows actual counts."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [1, 2],
            "errors": [{"issue": 3, "labels": ["a", "b"]}],
            "warnings": [],
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(
            label_changes,
            validation_results,
            repo_url,
            init_requested=True,
            validate_requested=True,
            gen_actions_requested=False,
        )

        assert "Issues initialized: 2" in result
        assert "Errors (multiple status labels): 1" in result
