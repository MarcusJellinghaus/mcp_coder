"""Tests for the CI check-and-fix workflow step (workflow_steps/ci.py)."""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflow_steps.ci import (
    CIFixConfig,
    _poll_for_ci_completion,
    _run_ci_analysis,
    _run_ci_fix,
)
from mcp_coder.workflow_steps.constants import (
    CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS,
    CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS,
    CI_MAX_POLL_ATTEMPTS,
)


class TestPollForCiCompletionHeartbeat:
    """Tests for elapsed time and heartbeat logging in _poll_for_ci_completion."""

    def test_heartbeat_logged_at_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """INFO heartbeat is logged every 8 iterations."""
        mock_ci_manager = MagicMock()
        in_progress: dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        # 9 in-progress responses, then completed on 10th
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 9 + [
            completed
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO, logger="mcp_coder.workflow_steps.ci"):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 1  # Fires at iteration 8

    def test_no_heartbeat_before_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No heartbeat logged when fewer than 8 iterations complete."""
        mock_ci_manager = MagicMock()
        in_progress: dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        # Only 5 in-progress, then completed
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 5 + [
            completed
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO, logger="mcp_coder.workflow_steps.ci"):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 0

    def test_elapsed_time_in_debug_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        in_progress: dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress, completed]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.DEBUG, logger="mcp_coder.workflow_steps.ci"):
                _poll_for_ci_completion(mock_ci_manager, "main")

        debug_logs = [
            r
            for r in caplog.records
            if "elapsed" in r.message.lower() and "in progress" in r.message.lower()
        ]
        assert len(debug_logs) >= 1

    def test_elapsed_time_in_no_run_found_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """'No CI run found yet' debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        empty_status: dict[str, Any] = {"run": {}, "jobs": []}
        completed: dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [empty_status, completed]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.DEBUG, logger="mcp_coder.workflow_steps.ci"):
                _poll_for_ci_completion(mock_ci_manager, "main")

        no_run_logs = [
            r
            for r in caplog.records
            if "no ci run found" in r.message.lower() and "elapsed" in r.message.lower()
        ]
        assert len(no_run_logs) >= 1

    def test_multiple_heartbeats_at_16_iterations(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Two heartbeats logged at iterations 8 and 16."""
        mock_ci_manager = MagicMock()
        in_progress: dict[str, Any] = {
            "run": {
                "status": "in_progress",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        completed: dict[str, Any] = {
            "run": {
                "status": "completed",
                "conclusion": "success",
                "run_ids": [1],
                "commit_sha": "abc123",
            },
            "jobs": [],
        }
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 17 + [
            completed
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO, logger="mcp_coder.workflow_steps.ci"):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [
            r for r in caplog.records if "CI polling heartbeat" in r.message
        ]
        assert len(heartbeat_logs) == 2  # Fires at iterations 8 and 16


class TestPollForCiCompletionShaCorrelation:
    """``expected_sha`` pins the poll to the commit the caller just pushed."""

    @staticmethod
    def _run(status: str, sha: str, conclusion: str | None = None) -> dict[str, Any]:
        """Build one ``get_latest_ci_status`` payload."""
        return {
            "run": {
                "status": status,
                "conclusion": conclusion,
                "run_ids": [1],
                "commit_sha": sha,
            },
            "jobs": [],
        }

    def test_green_run_for_an_earlier_commit_is_not_accepted(self) -> None:
        """The previous commit's completed green is skipped, not returned.

        For the first seconds after a push GitHub has not registered a run for
        the new commit yet, so "latest run on this branch" still answers with
        the old one. Taking its conclusion would mark the pushed commit green
        without CI ever having seen it.
        """
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            self._run("completed", "OLDSHA", conclusion="success"),
            self._run("queued", "NEWSHA"),
            self._run("completed", "NEWSHA", conclusion="success"),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(
                mock_ci_manager, "main", expected_sha="NEWSHA"
            )

        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "NEWSHA"
        assert mock_ci_manager.get_latest_ci_status.call_count == 3

    def test_red_run_for_an_earlier_commit_is_not_accepted_either(self) -> None:
        """A stale *failure* is skipped too - it is not this commit's result."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            self._run("completed", "OLDSHA", conclusion="failure"),
            self._run("completed", "NEWSHA", conclusion="success"),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(
                mock_ci_manager, "main", expected_sha="NEWSHA"
            )

        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "NEWSHA"

    def test_without_expected_sha_the_newest_run_still_wins(self) -> None:
        """Callers that did not just push keep today's behaviour."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            self._run("completed", "OLDSHA", conclusion="success"),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "OLDSHA"

    def test_expected_sha_that_never_appears_gives_up_on_its_own_budget(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A run that never appears costs ~105 seconds, not the full 12.5 minutes.

        No workflow triggered for the pushed commit (or another actor pushed
        past it) means the branch's newest run stays someone else's forever.
        Waiting out ``CI_MAX_POLL_ATTEMPTS`` for it would stall every caller,
        including ``implement``; the dedicated budget bounds it instead.
        """
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = self._run(
            "completed", "OLDSHA", conclusion="success"
        )

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(
                    mock_ci_manager, "main", expected_sha="NEWSHA"
                )

        assert status is None
        assert passed is True  # graceful exit, not a failure
        assert "No CI run appeared for" in caplog.text
        assert (
            mock_ci_manager.get_latest_ci_status.call_count
            == CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS
        )
        assert CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS < CI_MAX_POLL_ATTEMPTS

    def test_a_run_without_a_sha_is_accepted(self) -> None:
        """An uncorrelatable run is used rather than polled past to the cap."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success", "run_ids": [1]},
            "jobs": [],
        }

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(
                mock_ci_manager, "main", expected_sha="NEWSHA"
            )

        assert passed is True
        assert status is not None
        assert mock_ci_manager.get_latest_ci_status.call_count == 1


class TestPollForCiCompletionNoRunWithExpectedSha:
    """With ``expected_sha``, "no run" shares the expected-sha budget."""

    @staticmethod
    def _no_run() -> dict[str, Any]:
        """A status with no workflow run at all."""
        return {"run": {}, "jobs": []}

    @staticmethod
    def _run(status: str, sha: str, conclusion: str | None = None) -> dict[str, Any]:
        """Build one ``get_latest_ci_status`` payload."""
        return {
            "run": {
                "status": status,
                "conclusion": conclusion,
                "run_ids": [1],
                "commit_sha": sha,
            },
            "jobs": [],
        }

    def test_no_run_gives_up_on_expected_sha_budget(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No run ever appearing costs the small budget, not the full cap."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = self._no_run()

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(
                    mock_ci_manager, "main", expected_sha="NEWSHA"
                )

        assert status is None
        assert passed is True
        assert (
            mock_ci_manager.get_latest_ci_status.call_count
            == CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS
        )
        assert "CI_NOT_CONFIGURED" in caplog.text

    def test_no_run_and_other_commit_share_one_counter(self) -> None:
        """Alternating no-run and other-commit reads exhaust one shared budget."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            (
                self._no_run()
                if i % 2 == 0
                else self._run("completed", "OLDSHA", conclusion="success")
            )
            for i in range(CI_MAX_POLL_ATTEMPTS)
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(
                mock_ci_manager, "main", expected_sha="NEWSHA"
            )

        assert status is None
        assert passed is True
        assert (
            mock_ci_manager.get_latest_ci_status.call_count
            == CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS
        )

    def test_no_run_then_expected_run_succeeds(self) -> None:
        """A run for the expected commit after a short gap is accepted."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            self._no_run(),
            self._no_run(),
            self._run("completed", "NEWSHA", conclusion="success"),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(
                mock_ci_manager, "main", expected_sha="NEWSHA"
            )

        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "NEWSHA"
        assert mock_ci_manager.get_latest_ci_status.call_count == 3

    def test_lookup_failed_reads_do_not_count_against_expected_sha_budget(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Lookup-failed reads (empty ``run``) use their own cap only."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = (
            [{"run": {}, "jobs": [], "lookup_failed": True}] * 2
            + [self._no_run()] * (CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS - 1)
            + [self._run("completed", "NEWSHA", conclusion="success")]
        )

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(
                    mock_ci_manager, "main", expected_sha="NEWSHA"
                )

        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "NEWSHA"
        assert "CI_NOT_CONFIGURED" not in caplog.text

    def test_no_run_without_expected_sha_polls_full_cap(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Without ``expected_sha``, no-run still waits out the full cap."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = self._no_run()

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert status is None
        assert passed is True
        assert mock_ci_manager.get_latest_ci_status.call_count == CI_MAX_POLL_ATTEMPTS
        assert "CI_NOT_CONFIGURED" in caplog.text


class TestPollForCiCompletionLookupFailed:
    """``lookup_failed`` runs get their own small, bounded retry budget."""

    @staticmethod
    def _lookup_failed_run() -> dict[str, Any]:
        """A status carrying the swallowed-lookup-failure flag (mcp-workspace#318)."""
        return {"run": {}, "jobs": [], "lookup_failed": True}

    @staticmethod
    def _run(status: str, sha: str, conclusion: str | None = None) -> dict[str, Any]:
        """Build one normal ``get_latest_ci_status`` payload."""
        return {
            "run": {
                "status": status,
                "conclusion": conclusion,
                "run_ids": [1],
                "commit_sha": sha,
            },
            "jobs": [],
        }

    def test_lookup_failed_retries_then_succeeds(self) -> None:
        """Two lookup-failed reads, then a normal success, is accepted."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            self._lookup_failed_run(),
            self._lookup_failed_run(),
            self._run("completed", "SHA1", conclusion="success"),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep") as mock_sleep:
            status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert mock_ci_manager.get_latest_ci_status.call_count == 3
        assert mock_sleep.call_count == 2
        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "SHA1"

    def test_lookup_failed_exhausts_to_graceful_exit(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Exhausting the budget exits gracefully without a 4th call."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = self._lookup_failed_run()

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert (
            mock_ci_manager.get_latest_ci_status.call_count
            == CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS
        )
        assert status is None
        assert passed is True
        assert "lookup failed" in caplog.text
        assert "3" in caplog.text

    def test_lookup_failed_counter_resets_on_successful_read(self) -> None:
        """A non-lookup_failed read resets the counter before the next burst."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            self._lookup_failed_run(),
            self._lookup_failed_run(),
            self._run("in_progress", "SHA1"),
            self._lookup_failed_run(),
            self._lookup_failed_run(),
            self._lookup_failed_run(),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert mock_ci_manager.get_latest_ci_status.call_count == 6
        assert status is None
        assert passed is True

    def test_lookup_failed_checked_before_empty_run_branch(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """With an empty ``run``, the lookup-failed budget wins over the no-run one."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = self._lookup_failed_run()

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(
                    mock_ci_manager, "main", expected_sha="abc1234567890"
                )

        assert (
            mock_ci_manager.get_latest_ci_status.call_count
            == CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS
        )
        assert status is None
        assert passed is True
        assert "CI_API_ERROR" in caplog.text

    def test_lookup_failed_inside_run_is_not_a_lookup_failure(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The old shape (flag inside ``run``) is an in-progress run, not a failure."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {
            "run": {"lookup_failed": True},
            "jobs": [],
        }

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert mock_ci_manager.get_latest_ci_status.call_count == CI_MAX_POLL_ATTEMPTS
        assert status is None
        assert passed is True
        assert "CI_TIMEOUT: No completed run after polling" in caplog.text
        assert "CI_API_ERROR" not in caplog.text

    def test_lookup_failed_absent_key_behaves_as_before(self) -> None:
        """Regression guard: a genuinely empty run dict behaves as pre-#318."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = [
            {"run": {}, "jobs": []},
            self._run("completed", "SHA1", conclusion="success"),
        ]

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert mock_ci_manager.get_latest_ci_status.call_count == 2
        assert passed is True
        assert status is not None
        assert status["run"]["commit_sha"] == "SHA1"


def _make_config() -> CIFixConfig:
    """Build a minimal CIFixConfig for exercising the analysis/fix helpers."""
    return CIFixConfig(
        project_dir=Path("/test/project"),
        provider="claude",
        env_vars={},
        mcp_config=None,
        settings_file=None,
    )


def _make_failed_summary() -> dict[str, Any]:
    """Build a minimal failed-jobs summary for _run_ci_analysis."""
    return {
        "job_name": "build",
        "step_name": "pytest",
        "other_failed_jobs": [],
        "log_excerpt": "some failing log",
    }


class TestDefaultPromptHeaders:
    """Characterization: default headers reach get_prompt_with_substitutions."""

    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.get_prompt_with_substitutions")
    def test_analysis_uses_default_header(
        self,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
    ) -> None:
        """The analysis phase loads the "CI Failure Analysis Prompt" header."""
        mock_get_prompt.return_value = "analysis prompt"
        mock_prompt_llm.return_value = {"text": "analysis response"}

        _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

        header = mock_get_prompt.call_args.args[1]
        assert header == "CI Failure Analysis Prompt"

    @patch("mcp_coder.workflow_steps.ci.push_changes", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.commit_changes", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.run_formatters", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.get_prompt_with_substitutions")
    def test_fix_uses_default_header(
        self,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
        _mock_format: MagicMock,
        _mock_commit: MagicMock,
        _mock_push: MagicMock,
    ) -> None:
        """The fix phase loads the "CI Fix Prompt" header."""
        mock_get_prompt.return_value = "fix prompt"
        mock_prompt_llm.return_value = {"text": "fix response"}

        _run_ci_fix(_make_config(), "problem", fix_attempt=0)

        header = mock_get_prompt.call_args.args[1]
        assert header == "CI Fix Prompt"


class TestDefaultSessionDir:
    """Characterization: sessions stored under .mcp-coder/implement_sessions."""

    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch("mcp_coder.workflow_steps.ci.get_prompt_with_substitutions")
    def test_analysis_session_dir(
        self,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store: MagicMock,
    ) -> None:
        """Analysis sessions are stored under .mcp-coder/implement_sessions."""
        mock_get_prompt.return_value = "analysis prompt"
        mock_prompt_llm.return_value = {"text": "analysis response"}

        _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

        store_path = mock_store.call_args.kwargs["store_path"]
        assert store_path.endswith(str(Path(".mcp-coder") / "implement_sessions"))


class TestRunCiAnalysisPropagatesLlmFailures:
    """_run_ci_analysis re-raises the two typed LLM failures (Decision 9)."""

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_llm_timeout_propagates(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """LLMTimeoutError is NOT swallowed to None; it propagates out."""
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        with pytest.raises(LLMTimeoutError):
            _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_mcp_unavailable_propagates(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """McpServersUnavailableError is NOT swallowed to None; it propagates out."""
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        with pytest.raises(McpServersUnavailableError):
            _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

    @patch(
        "mcp_coder.workflow_steps.ci.prompt_llm",
        side_effect=RuntimeError("boom"),
    )
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    def test_generic_exception_still_soft_fails(
        self, _mock_prompt: MagicMock, _mock_prompt_llm: MagicMock
    ) -> None:
        """A generic exception is still soft-swallowed to None (unchanged)."""
        result = _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)
        assert result is None


class TestRunCiFixAbsorbsLlmFailures:
    """_run_ci_fix absorbs the two typed LLM failures into one failed attempt."""

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="fix prompt",
    )
    def test_llm_timeout_absorbed_as_false(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """LLMTimeoutError becomes a single failed attempt (return False)."""
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        result = _run_ci_fix(_make_config(), "problem", fix_attempt=0)
        assert result is False

    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="fix prompt",
    )
    def test_mcp_unavailable_absorbed_as_false(
        self, _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
    ) -> None:
        """McpServersUnavailableError becomes a single failed attempt (return False)."""
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        result = _run_ci_fix(_make_config(), "problem", fix_attempt=0)
        assert result is False
