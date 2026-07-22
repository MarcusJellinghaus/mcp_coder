"""Tests for get_failed_jobs_summary (shared CI log extraction)."""

from typing import cast

from mcp_coder.checks.branch_status import get_failed_jobs_summary
from mcp_coder.mcp_workspace_github import JobData


class TestGetFailedJobsSummary:
    """Tests for get_failed_jobs_summary function (shared CI log extraction)."""

    def test_single_failed_job_returns_details_with_step_info(self) -> None:
        """Single failed job should return its name, step info, and log."""
        jobs = cast(
            list[JobData],
            [
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
            ],
        )
        logs = {"test/3_Run tests.txt": "Error: test failed\nAssertionError"}

        result = get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["step_number"] == 3
        assert "Error: test failed" in result["log_excerpt"]
        assert result["other_failed_jobs"] == []

    def test_multiple_failed_jobs_returns_first_with_others_listed(self) -> None:
        """Multiple failed jobs should detail first, list others."""
        jobs = cast(
            list[JobData],
            [
                {
                    "name": "lint",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Run lint", "conclusion": "failure"}
                    ],
                },
                {
                    "name": "test",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Run tests", "conclusion": "failure"}
                    ],
                },
                {
                    "name": "build",
                    "conclusion": "failure",
                    "steps": [{"number": 1, "name": "Build", "conclusion": "failure"}],
                },
            ],
        )
        logs = {
            "lint/1_Run lint.txt": "Lint error",
            "test/1_Run tests.txt": "Test error",
            "build/1_Build.txt": "Build error",
        }

        result = get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == "lint"  # First failed job
        assert "Lint error" in result["log_excerpt"]
        assert "test" in result["other_failed_jobs"]
        assert "build" in result["other_failed_jobs"]
        assert len(result["other_failed_jobs"]) == 2

    def test_no_failed_jobs_returns_empty(self) -> None:
        """No failed jobs should return empty values."""
        jobs = cast(
            list[JobData],
            [
                {"name": "build", "conclusion": "success", "steps": []},
                {"name": "test", "conclusion": "success", "steps": []},
            ],
        )
        logs: dict[str, str] = {}

        result = get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == ""
        assert result["step_name"] == ""
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_failed_job_with_no_matching_log(self) -> None:
        """Failed job without matching log should return job/step info but empty excerpt."""
        jobs = cast(
            list[JobData],
            [
                {
                    "name": "test",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Run tests", "conclusion": "failure"}
                    ],
                }
            ],
        )
        logs: dict[str, str] = {}  # No logs available

        result = get_failed_jobs_summary(jobs, logs)

        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_constructs_correct_log_filename(self) -> None:
        """Should construct log filename from job name, step number, and step name.

        Note: Uses exact filename matching only (Decision 10). If no match found,
        log_excerpt will be empty and a warning is logged with expected/found filenames (Decision 16).
        """
        jobs = cast(
            list[JobData],
            [
                {
                    "name": "test",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Set up job", "conclusion": "success"},
                        {"number": 2, "name": "Run tests", "conclusion": "failure"},
                    ],
                }
            ],
        )
        # Log filename format: {job_name}/{step_number}_{step_name}.txt
        logs = {"test/2_Run tests.txt": "Test failure output"}

        result = get_failed_jobs_summary(jobs, logs)

        assert "Test failure output" in result["log_excerpt"]
