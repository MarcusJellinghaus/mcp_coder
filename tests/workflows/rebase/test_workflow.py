"""Fully-mocked tests for the ``run_rebase_workflow`` orchestrator.

Every exit-code path is exercised without touching a real repository, network,
or LLM. The orchestrator references its collaborators through module globals, so
each test patches the relevant names on ``mcp_coder.workflows.rebase`` and
asserts the resulting exit code plus the safety-net side effects (force-push,
reset-on-reject, abort-in-finally).
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import run_rebase_workflow

_SUCCESS_TEXT = "work done\nREBASE_OUTCOME: success\nREBASE_REASON: n/a"
_ABORTED_TEXT = "REBASE_OUTCOME: aborted\nREBASE_REASON: unresolvable conflict"


@pytest.fixture
def patched(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator to a benign happy-path default.

    Returns a namespace of the recordable mocks so individual tests can tweak
    return values / side effects and assert call arguments.
    """
    # Guards — all pass by default.
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: None)
    monkeypatch.setattr(
        rebase_module, "_resolve_base_branch", lambda _pd, _arg: ("main", None)
    )
    monkeypatch.setattr(
        rebase_module, "_check_pr_info_absent_on_base", lambda _pd, _b: None
    )

    fetch = MagicMock(return_value=True)
    needs = MagicMock(return_value=(True, "1 commit behind"))
    latest_sha = MagicMock(return_value="presha")
    monkeypatch.setattr(rebase_module, "fetch_remote", fetch)
    monkeypatch.setattr(rebase_module, "needs_rebase", needs)
    monkeypatch.setattr(rebase_module, "get_latest_commit_sha", latest_sha)

    # LLM session infrastructure — kept offline.
    monkeypatch.setattr(rebase_module, "prepare_llm_environment", lambda _pd: {})
    monkeypatch.setattr(rebase_module, "get_prompt", lambda _s, _h: "PROMPT")
    monkeypatch.setattr(
        rebase_module, "get_branch_name_for_logging", lambda _pd: "feature"
    )
    prompt_llm = MagicMock(return_value={"text": _SUCCESS_TEXT})
    monkeypatch.setattr(rebase_module, "prompt_llm", prompt_llm)

    # Git-state helpers used by the decision + safety net.
    mid_rebase = MagicMock(return_value=False)
    success_shape = MagicMock(return_value=True)
    abort = MagicMock()
    reset = MagicMock()
    push = MagicMock(return_value={"success": True, "error": None})
    monkeypatch.setattr(rebase_module, "_is_rebase_in_progress", mid_rebase)
    monkeypatch.setattr(rebase_module, "_rebase_success_shape", success_shape)
    monkeypatch.setattr(rebase_module, "_abort_rebase", abort)
    monkeypatch.setattr(rebase_module, "_reset_hard", reset)
    monkeypatch.setattr(rebase_module, "git_push", push)

    return SimpleNamespace(
        prompt_llm=prompt_llm,
        fetch=fetch,
        needs=needs,
        mid_rebase=mid_rebase,
        success_shape=success_shape,
        abort=abort,
        reset=reset,
        push=push,
    )


def _run(tmp_path: Path, base_branch: str | None = None) -> int:
    return run_rebase_workflow(tmp_path, provider="claude", base_branch=base_branch)


def test_preflight_error_returns_2_without_llm(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing pre-flight short-circuits to ``2`` and never calls the LLM."""
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: "dirty tree")

    assert _run(tmp_path) == 2
    patched.prompt_llm.assert_not_called()


def test_non_standard_base_without_arg_returns_2(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A base-branch guard error maps to ``2`` and never calls the LLM."""
    monkeypatch.setattr(
        rebase_module,
        "_resolve_base_branch",
        lambda _pd, _arg: (None, "Non-standard base 'develop'; pass --base-branch"),
    )

    assert _run(tmp_path) == 2
    patched.prompt_llm.assert_not_called()


def test_no_op_when_not_needed_returns_0_without_llm(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """``needs_rebase`` False (up-to-date) short-circuits to ``0`` with no LLM."""
    patched.needs.return_value = (False, "up-to-date")

    assert _run(tmp_path) == 0
    patched.prompt_llm.assert_not_called()


def test_needs_rebase_error_reason_returns_2_without_llm(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """``needs_rebase`` False with an ``error:`` reason maps to ``2``, not ``0``."""
    patched.needs.return_value = (
        False,
        "error: target branch 'origin/main' not found",
    )

    assert _run(tmp_path) == 2
    patched.prompt_llm.assert_not_called()


def test_pr_info_present_on_base_returns_2(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``pr_info/`` present on the base branch maps to ``2`` before any LLM call."""
    monkeypatch.setattr(
        rebase_module,
        "_check_pr_info_absent_on_base",
        lambda _pd, _b: "pr_info/ present on origin/main",
    )

    assert _run(tmp_path) == 2
    patched.prompt_llm.assert_not_called()


def test_success_marker_and_shape_pushes_and_returns_0(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Success marker + success shape + push success → ``0`` (force-with-lease)."""
    assert _run(tmp_path) == 0
    patched.push.assert_called_once()
    _args, kwargs = patched.push.call_args
    assert kwargs.get("force_with_lease") is True
    patched.reset.assert_not_called()


def test_aborted_marker_overrides_success_shape_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """An ``aborted`` marker blocks the push and yields ``1`` even if shape is OK."""
    patched.prompt_llm.return_value = {"text": _ABORTED_TEXT}

    assert _run(tmp_path) == 1
    patched.push.assert_not_called()


def test_mid_rebase_after_session_returns_1_and_aborts(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Still mid-rebase after the session → ``1`` and the finally-net aborts."""
    patched.mid_rebase.return_value = True

    assert _run(tmp_path) == 1
    patched.push.assert_not_called()
    patched.abort.assert_called_once()


def test_push_rejected_resets_and_returns_2(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A rejected force-push restores ``pre_sha`` and maps to ``2``."""
    patched.push.return_value = {"success": False, "error": "stale info"}

    assert _run(tmp_path) == 2
    patched.reset.assert_called_once_with(tmp_path, "presha")


def test_llm_timeout_returns_1(patched: SimpleNamespace, tmp_path: Path) -> None:
    """An ``LLMTimeoutError`` from the session is caught and mapped to ``1``."""
    patched.prompt_llm.side_effect = LLMTimeoutError("no output for 600s")

    assert _run(tmp_path) == 1
    patched.push.assert_not_called()


def test_llm_timeout_mid_rebase_aborts_in_finally(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A session failure that leaves a rebase in progress is aborted by finally."""
    patched.prompt_llm.side_effect = LLMTimeoutError("no output for 600s")
    patched.mid_rebase.return_value = True

    assert _run(tmp_path) == 1
    patched.abort.assert_called_once()
