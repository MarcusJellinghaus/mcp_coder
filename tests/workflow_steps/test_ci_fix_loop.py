"""Tests for the ``check_and_fix_ci`` fix loop, driven through its real phases."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import ci, commit
from mcp_coder.workflow_steps.commit import PUSH_REJECTED_ERROR, PushRejectedError
from mcp_coder.workflow_steps.constants import CI_MAX_FIX_ATTEMPTS
from tests.ci_fix_drive import patch_ci_fix_externals


def _rejected_push_error(reason: str) -> str:
    """Build a push error shaped like a stringified ``GitCommandError``."""
    return (
        "Git error during push: Cmd('git') failed due to: exit code(1)\n"
        "  cmdline: git push origin feature\n"
        "  stderr: 'To https://github.com/owner/repo.git\n"
        f" ! [rejected]        feature -> feature ({reason})\n"
        "error: failed to push some refs to 'https://github.com/owner/repo.git'\n"
        "hint: Updates were rejected because the remote contains work that you do\n"
        "hint: not have locally.'"
    )


@pytest.fixture(name="prompt_llm")
def fixture_prompt_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the fix loop's externals and return the ``prompt_llm`` mock."""
    patch_ci_fix_externals(monkeypatch)
    monkeypatch.setattr(ci, "run_formatters", MagicMock(return_value=True))
    prompt_llm: MagicMock = vars(ci)["prompt_llm"]
    return prompt_llm


class TestRejectedPush:
    """A push rejected because the branch moved stops the loop at once."""

    @pytest.mark.parametrize("reason", ["fetch first", "non-fast-forward"])
    def test_raises_after_one_attempt(
        self,
        prompt_llm: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        reason: str,
    ) -> None:
        """The error leaves check_and_fix_ci with no further LLM calls."""
        monkeypatch.setattr(ci, "push_changes", commit.push_changes)
        monkeypatch.setattr(
            commit,
            "git_push",
            MagicMock(
                return_value={"success": False, "error": _rejected_push_error(reason)}
            ),
        )

        with pytest.raises(PushRejectedError, match=PUSH_REJECTED_ERROR):
            ci.check_and_fix_ci(tmp_path, "feature", "claude")

        assert prompt_llm.call_count == 2  # one analysis, one fix

    def test_push_requests_rejection_detection(
        self,
        prompt_llm: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The fix phase opts in to rejected-push detection."""
        push_changes = MagicMock(return_value=True)
        monkeypatch.setattr(ci, "push_changes", push_changes)

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is True

        push_changes.assert_called_once_with(tmp_path, raise_on_rejected=True)
        assert prompt_llm.call_count == 2


class TestOtherPushFailure:
    """A push failure that is not a rejection keeps retrying."""

    def test_continues_until_attempts_run_out(
        self,
        prompt_llm: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Each attempt runs analysis and fix, and the loop ends as False."""
        monkeypatch.setattr(ci, "push_changes", MagicMock(return_value=False))

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is False

        assert prompt_llm.call_count == 2 * CI_MAX_FIX_ATTEMPTS


class TestEmptyAnalysis:
    """An empty analysis consumes one attempt, whichever attempt it is."""

    def test_every_attempt_empty_ends_as_false(
        self,
        prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The whole budget is spent on analysis and nothing is committed."""
        prompt_llm.return_value = {"text": ""}

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is False

        assert prompt_llm.call_count == CI_MAX_FIX_ATTEMPTS
        vars(ci)["commit_changes"].assert_not_called()

    def test_later_attempt_continues(
        self,
        prompt_llm: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Attempt 2 asks for the next attempt instead of exiting as success."""
        prompt_llm.return_value = {"text": ""}
        manager = vars(ci)["CIResultsManager"].return_value
        config = ci.CIFixConfig(
            project_dir=tmp_path, provider="claude", env_vars={}, mcp_config=None
        )

        result = ci._run_ci_analysis_and_fix(
            config,
            manager.get_latest_ci_status.return_value,
            manager,
            fix_attempt=1,
        )

        assert result == (True, None)
