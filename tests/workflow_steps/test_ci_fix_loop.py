"""Tests for the ``check_and_fix_ci`` fix loop, driven through its real phases."""

from collections.abc import Mapping
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import ci, ci_fix_helpers, commit
from mcp_coder.workflow_steps.commit import PUSH_REJECTED_ERROR, PushRejectedError
from mcp_coder.workflow_steps.constants import CI_MAX_FIX_ATTEMPTS, COMMIT_MESSAGE_FILE
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


def _status(*, dirty: bool) -> dict[str, object]:
    """Build a ``get_working_tree_status`` result."""
    return {
        "success": True,
        "staged": [],
        "modified": ["src/module.py"] if dirty else [],
        "untracked": [],
    }


_NEW_FAILED_RUN = {
    "run": {"run_ids": [2], "status": "completed", "conclusion": "failure"},
    "jobs": [
        {
            "name": "test",
            "conclusion": "failure",
            "run_id": 2,
            "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
        }
    ],
}
_NEW_GREEN_RUN = {
    "run": {"run_ids": [2], "status": "completed", "conclusion": "success"},
    "jobs": [],
}


@pytest.fixture(name="read_status")
def fixture_read_status(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the helpers' git reads: a clean tree and a fixed HEAD."""
    read_status = MagicMock(return_value=_status(dirty=False))
    monkeypatch.setattr(ci_fix_helpers, "get_working_tree_status", read_status)
    monkeypatch.setattr(
        ci_fix_helpers, "get_latest_commit_sha", MagicMock(return_value="SHA")
    )
    return read_status


def _first_attempt_dirty(read_status: MagicMock, commit_changes: MagicMock) -> None:
    """Make the tree dirty until ``commit_changes`` runs, as a real commit would."""

    def commit(*_args: object, **_kwargs: object) -> bool:
        read_status.return_value = _status(dirty=False)
        return True

    read_status.return_value = _status(dirty=True)
    commit_changes.side_effect = commit


def _set_later_runs(*runs: Mapping[str, object]) -> None:
    """Queue what CI reports after the initial failed run."""
    manager = vars(ci)["CIResultsManager"].return_value
    failed_run = manager.get_latest_ci_status.return_value
    manager.get_latest_ci_status.side_effect = [failed_run, *runs]


class TestNoChangeFix:
    """A fix that changes nothing consumes one attempt."""

    def test_clean_tree_every_attempt_ends_as_false(
        self,
        prompt_llm: MagicMock,
        read_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Nothing is committed or pushed, and red CI is not reported as green."""
        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is False

        assert prompt_llm.call_count == 2 * CI_MAX_FIX_ATTEMPTS
        assert read_status.call_count == CI_MAX_FIX_ATTEMPTS
        vars(ci)["commit_changes"].assert_not_called()
        vars(ci)["push_changes"].assert_not_called()

    @pytest.mark.usefixtures("prompt_llm")
    def test_formatter_only_change_commits(
        self,
        read_status: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """A tree dirtied only by the formatters still counts as a change."""

        def format_tree(_project_dir: Path) -> bool:
            read_status.return_value = _status(dirty=True)
            return True

        monkeypatch.setattr(ci, "run_formatters", MagicMock(side_effect=format_tree))

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is True

        vars(ci)["commit_changes"].assert_called_once()
        vars(ci)["push_changes"].assert_called_once()

    @pytest.mark.usefixtures("prompt_llm")
    def test_real_fix_leaves_message_file(
        self,
        read_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A prepared message file is still there when the commit runs."""
        message_file = tmp_path / COMMIT_MESSAGE_FILE
        message_file.parent.mkdir(parents=True)
        message_file.write_text("fix: something\n", encoding="utf-8")
        seen: list[bool] = []

        def commit(*_args: object, **_kwargs: object) -> bool:
            seen.append(message_file.exists())
            return True

        vars(ci)["commit_changes"].side_effect = commit
        read_status.return_value = _status(dirty=True)

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is True

        assert seen == [True]


class TestPushRetry:
    """A no-change attempt retries a push that failed on an earlier attempt."""

    @pytest.mark.usefixtures("prompt_llm")
    def test_failed_push_then_no_change_retries_push(
        self,
        read_status: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The retry commits nothing new, then waits for the new run as usual."""
        commit_changes = vars(ci)["commit_changes"]
        _first_attempt_dirty(read_status, commit_changes)
        push_changes = MagicMock(side_effect=[False, True])
        monkeypatch.setattr(ci, "push_changes", push_changes)
        _set_later_runs(_NEW_GREEN_RUN, _NEW_GREEN_RUN)

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is True

        commit_changes.assert_called_once()
        assert push_changes.call_count == 2

    @pytest.mark.usefixtures("prompt_llm")
    def test_rejected_retry_propagates(
        self,
        read_status: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """A rejection on the retry stops the loop like any other rejection."""
        _first_attempt_dirty(read_status, vars(ci)["commit_changes"])
        rejection = PushRejectedError(PUSH_REJECTED_ERROR)
        monkeypatch.setattr(
            ci, "push_changes", MagicMock(side_effect=[False, rejection])
        )

        with pytest.raises(PushRejectedError, match=PUSH_REJECTED_ERROR):
            ci.check_and_fix_ci(tmp_path, "feature", "claude")

    @pytest.mark.usefixtures("prompt_llm")
    def test_successful_retry_clears_state(
        self,
        read_status: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """After the retry lands, a later no-change attempt does not push."""
        assert CI_MAX_FIX_ATTEMPTS >= 3
        _first_attempt_dirty(read_status, vars(ci)["commit_changes"])
        push_changes = MagicMock(side_effect=[False, True])
        monkeypatch.setattr(ci, "push_changes", push_changes)
        _set_later_runs(_NEW_FAILED_RUN, _NEW_FAILED_RUN)

        assert ci.check_and_fix_ci(tmp_path, "feature", "claude") is False

        assert push_changes.call_count == 2
