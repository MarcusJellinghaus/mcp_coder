"""Tests for check_and_fix_ci and _read_problem_description (workflow_steps/ci.py)."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch


class TestCheckAndFixCI:
    """Tests for check_and_fix_ci function."""

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    @patch("mcp_coder.workflow_steps.ci.time.sleep")
    def test_ci_passes_first_check_returns_true(
        self, mock_sleep: MagicMock, mock_ci_manager: MagicMock
    ) -> None:
        """When CI passes on first check, should return True immediately."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

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
        )

        assert result is True
        mock_sleep.assert_not_called()  # No polling needed

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    @patch("mcp_coder.workflow_steps.ci.time.sleep")
    def test_ci_not_found_warns_and_returns_true(
        self, mock_sleep: MagicMock, mock_ci_manager: MagicMock
    ) -> None:
        """When no CI run found after polling, should warn and return True (exit 0)."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

        # Setup mock - always returns empty (no CI run)
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
        )

        assert result is True  # Graceful exit

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.run_formatters")
    @patch("mcp_coder.workflow_steps.ci.commit_changes")
    @patch("mcp_coder.workflow_steps.ci.push_changes")
    @patch("mcp_coder.workflow_steps.ci.time.sleep")
    def test_ci_fails_fix_succeeds_returns_true(
        self,
        mock_sleep: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_format: MagicMock,
        mock_store_session: MagicMock,
        mock_llm: MagicMock,
        mock_ci_manager: MagicMock,
    ) -> None:
        """When CI fails but fix succeeds, should return True."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager

        # First call: CI failed, Second call (after fix): CI passed
        mock_manager.get_latest_ci_status.side_effect = [
            {
                "run": {"run_ids": [1], "status": "completed", "conclusion": "failure"},
                "jobs": [
                    {
                        "name": "test",
                        "conclusion": "failure",
                        "run_id": 1,
                        "steps": [
                            {"number": 1, "name": "Run tests", "conclusion": "failure"}
                        ],
                    }
                ],
            },
            # After fix - new CI run (different id) started but in progress
            {
                "run": {"run_ids": [2], "status": "in_progress", "conclusion": None},
                "jobs": [],
            },
            # New CI run completed with success
            {
                "run": {"run_ids": [2], "status": "completed", "conclusion": "success"},
                "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
            },
        ]
        mock_manager.get_run_logs.return_value = {
            "test/1_Run tests.txt": "Error: test failed"
        }

        mock_llm.return_value = {
            "text": "Analysis complete",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
        )

        assert result is True

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.run_formatters")
    @patch("mcp_coder.workflow_steps.ci.commit_changes")
    @patch("mcp_coder.workflow_steps.ci.push_changes")
    @patch("mcp_coder.workflow_steps.ci.time.sleep")
    def test_max_attempts_exhausted_returns_false(
        self,
        mock_sleep: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_format: MagicMock,
        mock_store_session: MagicMock,
        mock_llm: MagicMock,
        mock_ci_manager: MagicMock,
    ) -> None:
        """When max fix attempts exhausted, should return False (exit 1)."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager

        # Helper to create failed CI status with given run ID
        def make_failed_status(run_id: int) -> dict[str, Any]:
            return {
                "run": {
                    "run_ids": [run_id],
                    "status": "completed",
                    "conclusion": "failure",
                },
                "jobs": [
                    {
                        "name": "test",
                        "conclusion": "failure",
                        "run_id": run_id,
                        "steps": [
                            {"number": 1, "name": "Run tests", "conclusion": "failure"}
                        ],
                    }
                ],
            }

        # Simulate 4 fix attempts all failing with new CI runs each time
        # Flow: initial poll -> fix 1 -> wait for new run -> poll -> fix 2 -> ...
        mock_manager.get_latest_ci_status.side_effect = [
            make_failed_status(1),  # Initial poll
            make_failed_status(2),  # After fix 1: wait_for_new detects new run
            make_failed_status(2),  # poll_for_completion
            make_failed_status(3),  # After fix 2: wait_for_new detects new run
            make_failed_status(3),  # poll_for_completion
            make_failed_status(4),  # After fix 3: wait_for_new detects new run
            make_failed_status(4),  # poll_for_completion
            make_failed_status(5),  # After fix 4: wait_for_new detects new run
            make_failed_status(5),  # poll_for_completion (final failure)
        ]
        mock_manager.get_run_logs.return_value = {"test/1_Run tests.txt": "Error"}

        mock_llm.return_value = {
            "text": "Analysis/fix response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
        )

        assert result is False  # Max attempts exhausted

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    def test_api_error_returns_true_gracefully(
        self, mock_ci_manager: MagicMock
    ) -> None:
        """When API errors occur, should return True with warning (exit 0)."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = Exception("API Error")

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
        )

        assert result is True  # Graceful handling

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.run_formatters")
    @patch("mcp_coder.workflow_steps.ci.commit_changes")
    @patch("mcp_coder.workflow_steps.ci.push_changes")
    @patch("mcp_coder.workflow_steps.ci.time.sleep")
    def test_git_push_error_returns_false(
        self,
        mock_sleep: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_format: MagicMock,
        mock_store_session: MagicMock,
        mock_llm: MagicMock,
        mock_ci_manager: MagicMock,
    ) -> None:
        """When git push fails during fix, should return False (fail fast)."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"run_ids": [1], "status": "completed", "conclusion": "failure"},
            "jobs": [
                {
                    "name": "test",
                    "conclusion": "failure",
                    "run_id": 1,
                    "steps": [
                        {"number": 1, "name": "Run tests", "conclusion": "failure"}
                    ],
                }
            ],
        }
        mock_manager.get_run_logs.return_value = {
            "test/1_Run tests.txt": "Error: test failed"
        }

        mock_llm.return_value = {
            "text": "Analysis/fix complete",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = False  # Git push fails

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
        )

        assert result is False  # Fail fast on git errors

    @patch("mcp_coder.workflow_steps.ci.CIResultsManager")
    @patch("mcp_coder.workflow_steps.ci.time.sleep")
    def test_ci_in_progress_waits_for_completion(
        self, mock_sleep: MagicMock, mock_ci_manager: MagicMock
    ) -> None:
        """When CI is in progress, should poll until completed."""
        from mcp_coder.workflow_steps.ci import check_and_fix_ci

        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager

        # First call: in progress, Second call: completed with success
        mock_manager.get_latest_ci_status.side_effect = [
            {
                "run": {"run_ids": [1], "status": "in_progress", "conclusion": None},
                "jobs": [],
            },
            {
                "run": {"run_ids": [1], "status": "completed", "conclusion": "success"},
                "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
            },
        ]

        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            provider="claude",
        )

        assert result is True
        # Should have slept while waiting for CI
        assert mock_sleep.call_count >= 1


class TestReadProblemDescription:
    """Tests for _read_problem_description function."""

    def test_empty_file_uses_fallback(self, tmp_path: Path) -> None:
        """Empty temp file should return fallback response."""
        from mcp_coder.workflow_steps.ci import (
            _read_problem_description,
        )

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("")  # Empty file

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
        assert not temp_file.exists()  # File should be deleted

    def test_whitespace_only_file_uses_fallback(self, tmp_path: Path) -> None:
        """File with only whitespace should return fallback response."""
        from mcp_coder.workflow_steps.ci import (
            _read_problem_description,
        )

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("   \n\t\n  ")  # Whitespace only

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
        assert not temp_file.exists()

    def test_file_with_content_returns_content(self, tmp_path: Path) -> None:
        """File with content should return that content."""
        from mcp_coder.workflow_steps.ci import (
            _read_problem_description,
        )

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("Problem: test failed")

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "Problem: test failed"
        assert not temp_file.exists()

    def test_missing_file_uses_fallback(self, tmp_path: Path) -> None:
        """Missing temp file should return fallback response."""
        from mcp_coder.workflow_steps.ci import (
            _read_problem_description,
        )

        temp_file = tmp_path / ".ci_problem_description.md"
        # Don't create the file

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
