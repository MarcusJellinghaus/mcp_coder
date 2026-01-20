"""Tests for CI check helper functions."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

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


class TestCheckAndFixCI:
    """Tests for check_and_fix_ci function."""

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_passes_first_check_returns_true(
        self, mock_sleep: MagicMock, mock_ci_manager: MagicMock
    ) -> None:
        """When CI passes on first check, should return True immediately."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        # Setup mock
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
        }

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is True
        mock_sleep.assert_not_called()  # No polling needed

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_not_found_warns_and_returns_true(
        self, mock_sleep: MagicMock, mock_ci_manager: MagicMock
    ) -> None:
        """When no CI run found after polling, should warn and return True (exit 0)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        # Setup mock - always returns empty (no CI run)
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is True  # Graceful exit

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.run_formatters")
    @patch("mcp_coder.workflows.implement.core.commit_changes")
    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_fails_fix_succeeds_returns_true(
        self,
        mock_sleep: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_format: MagicMock,
        mock_llm: MagicMock,
        mock_ci_manager: MagicMock,
    ) -> None:
        """When CI fails but fix succeeds, should return True."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager

        # First call: CI failed, Second call (after fix): CI passed
        mock_manager.get_latest_ci_status.side_effect = [
            {
                "run": {"id": 1, "status": "completed", "conclusion": "failure"},
                "jobs": [
                    {
                        "name": "test",
                        "conclusion": "failure",
                        "steps": [
                            {"number": 1, "name": "Run tests", "conclusion": "failure"}
                        ],
                    }
                ],
            },
            # After fix - new CI run (different id) started but in progress
            {
                "run": {"id": 2, "status": "in_progress", "conclusion": None},
                "jobs": [],
            },
            # New CI run completed with success
            {
                "run": {"id": 2, "status": "completed", "conclusion": "success"},
                "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
            },
        ]
        mock_manager.get_run_logs.return_value = {
            "test/1_Run tests.txt": "Error: test failed"
        }

        mock_llm.return_value = "Analysis complete"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is True

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.run_formatters")
    @patch("mcp_coder.workflows.implement.core.commit_changes")
    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_max_attempts_exhausted_returns_false(
        self,
        mock_sleep: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_format: MagicMock,
        mock_llm: MagicMock,
        mock_ci_manager: MagicMock,
    ) -> None:
        """When max fix attempts exhausted, should return False (exit 1)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager

        # Always return failed CI - simulates 3 fix attempts all failing
        failed_status = {
            "run": {"id": 1, "status": "completed", "conclusion": "failure"},
            "jobs": [
                {
                    "name": "test",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Run tests", "conclusion": "failure"}
                    ],
                }
            ],
        }
        # Return failed status repeatedly for all 3 attempts
        # Each fix cycle: initial check, then detect new run, then check new run result
        mock_manager.get_latest_ci_status.return_value = failed_status
        mock_manager.get_run_logs.return_value = {"test/1_Run tests.txt": "Error"}

        mock_llm.return_value = "Analysis/fix response"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is False  # Max attempts exhausted

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    def test_api_error_returns_true_gracefully(
        self, mock_ci_manager: MagicMock
    ) -> None:
        """When API errors occur, should return True with warning (exit 0)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = Exception("API Error")

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is True  # Graceful handling

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.run_formatters")
    @patch("mcp_coder.workflows.implement.core.commit_changes")
    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_git_push_error_returns_false(
        self,
        mock_sleep: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_format: MagicMock,
        mock_llm: MagicMock,
        mock_ci_manager: MagicMock,
    ) -> None:
        """When git push fails during fix, should return False (fail fast)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"id": 1, "status": "completed", "conclusion": "failure"},
            "jobs": [
                {
                    "name": "test",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Run tests", "conclusion": "failure"}
                    ],
                }
            ],
        }
        mock_manager.get_run_logs.return_value = {
            "test/1_Run tests.txt": "Error: test failed"
        }

        mock_llm.return_value = "Analysis/fix complete"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = False  # Git push fails

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is False  # Fail fast on git errors

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_in_progress_waits_for_completion(
        self, mock_sleep: MagicMock, mock_ci_manager: MagicMock
    ) -> None:
        """When CI is in progress, should poll until completed."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager

        # First call: in progress, Second call: completed with success
        mock_manager.get_latest_ci_status.side_effect = [
            {
                "run": {"id": 1, "status": "in_progress", "conclusion": None},
                "jobs": [],
            },
            {
                "run": {"id": 1, "status": "completed", "conclusion": "success"},
                "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
            },
        ]

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
            method="api",
        )

        assert result is True
        # Should have slept while waiting for CI
        assert mock_sleep.call_count >= 1


class TestReadProblemDescription:
    """Tests for _read_problem_description function."""

    def test_empty_file_uses_fallback(self, tmp_path: Path) -> None:
        """Empty temp file should return fallback response."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("")  # Empty file

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
        assert not temp_file.exists()  # File should be deleted

    def test_whitespace_only_file_uses_fallback(self, tmp_path: Path) -> None:
        """File with only whitespace should return fallback response."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("   \n\t\n  ")  # Whitespace only

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
        assert not temp_file.exists()

    def test_file_with_content_returns_content(self, tmp_path: Path) -> None:
        """File with content should return that content."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("Problem: test failed")

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "Problem: test failed"
        assert not temp_file.exists()

    def test_missing_file_uses_fallback(self, tmp_path: Path) -> None:
        """Missing temp file should return fallback response."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        # Don't create the file

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
