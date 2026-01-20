"""Tests for CI check helper functions."""

from typing import Any

from mcp_coder.workflows.implement.core import (
    _extract_log_excerpt,
    _get_failed_jobs_summary,
)


class TestExtractLogExcerpt:
    """Tests for _extract_log_excerpt function."""

    def test_short_log_returned_unchanged(self) -> None:
        """Logs under 200 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(100)])

        result = _extract_log_excerpt(log)

        assert result == log

    def test_exactly_200_lines_returned_unchanged(self) -> None:
        """Logs of exactly 200 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(200)])

        result = _extract_log_excerpt(log)

        assert result == log

    def test_long_log_truncated_to_first_30_last_170(self) -> None:
        """Logs over 200 lines should have first 30 + last 170 lines."""
        log = "\n".join([f"Line {i}" for i in range(300)])

        result = _extract_log_excerpt(log)

        # Should have 200 lines + truncation marker
        assert "Line 0" in result  # First line preserved
        assert "Line 29" in result  # Line 30 preserved (0-indexed)
        assert "Line 299" in result  # Last line preserved
        assert "Line 130" in result  # From last 170 (300-170=130)
        assert "Line 30" not in result  # Should be truncated
        assert "Line 129" not in result  # Should be truncated
        assert "..." in result or "[truncated]" in result.lower()

    def test_empty_log_returns_empty(self) -> None:
        """Empty log should return empty string."""
        result = _extract_log_excerpt("")

        assert result == ""


class TestGetFailedJobsSummary:
    """Tests for _get_failed_jobs_summary function."""

    def test_single_failed_job_returns_details_with_step_info(self) -> None:
        """Single failed job should return its name, step info, and log."""
        jobs: list[dict[str, Any]] = [
            {"name": "build", "conclusion": "success", "steps": []},
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"number": 1, "name": "Set up job", "conclusion": "success"},
                    {"number": 2, "name": "Checkout", "conclusion": "success"},
                    {"number": 3, "name": "Run tests", "conclusion": "failure"},
                ],
            },
        ]
        logs = {"test/3_Run tests.txt": "Error: test failed\nAssertionError"}

        result = _get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["step_number"] == 3
        assert "Error: test failed" in result["log_excerpt"]
        assert result["other_failed_jobs"] == []

    def test_multiple_failed_jobs_returns_first_with_others_listed(self) -> None:
        """Multiple failed jobs should detail first, list others."""
        jobs: list[dict[str, Any]] = [
            {
                "name": "lint",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run lint", "conclusion": "failure"}],
            },
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
            },
            {
                "name": "build",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Build", "conclusion": "failure"}],
            },
        ]
        logs = {
            "lint/1_Run lint.txt": "Lint error",
            "test/1_Run tests.txt": "Test error",
            "build/1_Build.txt": "Build error",
        }

        result = _get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == "lint"  # First failed job
        assert "Lint error" in result["log_excerpt"]
        assert "test" in result["other_failed_jobs"]
        assert "build" in result["other_failed_jobs"]
        assert len(result["other_failed_jobs"]) == 2

    def test_no_failed_jobs_returns_empty(self) -> None:
        """No failed jobs should return empty values."""
        jobs: list[dict[str, Any]] = [
            {"name": "build", "conclusion": "success", "steps": []},
            {"name": "test", "conclusion": "success", "steps": []},
        ]
        logs: dict[str, str] = {}

        result = _get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == ""
        assert result["step_name"] == ""
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_failed_job_with_no_matching_log(self) -> None:
        """Failed job without matching log should return job/step info but empty excerpt."""
        jobs: list[dict[str, Any]] = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
            }
        ]
        logs: dict[str, str] = {}  # No logs available

        result = _get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_constructs_correct_log_filename(self) -> None:
        """Should construct log filename from job name, step number, and step name.

        Note: Uses exact filename matching only (Decision 10). If no match found,
        log_excerpt will be empty and a warning is logged with expected/found filenames (Decision 16).
        """
        jobs: list[dict[str, Any]] = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"number": 1, "name": "Set up job", "conclusion": "success"},
                    {"number": 2, "name": "Run tests", "conclusion": "failure"},
                ],
            }
        ]
        # Log filename format: {job_name}/{step_number}_{step_name}.txt
        logs = {"test/2_Run tests.txt": "Test failure output"}

        result = _get_failed_jobs_summary(jobs, logs)

        assert "Test failure output" in result["log_excerpt"]
