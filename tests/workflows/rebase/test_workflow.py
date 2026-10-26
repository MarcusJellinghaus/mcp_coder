"""Fully-mocked tests for the ``run_rebase_workflow`` orchestrator.

Python drives every git operation and every check; the LLM is consulted only
for conflict resolution and regression fixes. Every exit-code path is
exercised without touching a real repository, network, or LLM: each test
patches the orchestrator's collaborators on ``mcp_coder.workflows.rebase``
(git helpers, check runner, LLM session helper, push) and asserts the exit
code plus the safety-net side effects (force-push, reset, abort-in-finally)
and OUTPUT-level progress logging.
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflow_steps import commit as commit_module
from mcp_coder.workflow_steps import rebase as rebase_step_module
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import (
    _check_pr_info_absent_on_base,
    _preflight,
    _rebase_success_shape,
    run_rebase_workflow,
)
from mcp_coder.workflows.rebase_checks import CheckRunError, FailureKey

_REAL_PREFLIGHT = _preflight
_REAL_PR_INFO_GUARD = _check_pr_info_absent_on_base
_REAL_SUCCESS_SHAPE = _rebase_success_shape

_COMPLETED: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
    "status": "completed",
}
_STOPPED: dict[str, Any] = {
    **_COMPLETED,
    "success": False,
    "returncode": 1,
    "stderr": "CONFLICT",
    "status": "stopped_on_conflict",
}
_REBASE_ERROR: dict[str, Any] = {
    **_COMPLETED,
    "success": False,
    "error": "git rebase origin/main failed (exit 128)",
    "returncode": 128,
    "stderr": "boom",
    "status": "error",
}


def _blob_info(*paths: str, binary: tuple[str, ...] = ()) -> dict[str, Any]:
    """Build a successful ``get_conflict_blob_info`` result for ``paths``."""
    return {
        "success": True,
        "error": None,
        "returncode": 0,
        "stderr": "",
        "entries": [
            {"path": p, "stages": [1, 2, 3], "is_binary": p in binary} for p in paths
        ],
    }


_GIT_OK: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
}
_GIT_FAIL: dict[str, Any] = {
    "success": False,
    "error": "git reset --hard failed (exit 128)",
    "returncode": 128,
    "stderr": "fatal: bad revision",
}
_CLEAN_STATUS: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
    "clean": True,
    "staged": [],
    "modified": [],
    "untracked": [],
}
_FAILED_STATUS = {**_CLEAN_STATUS, "success": False, "clean": False}

_REGRESSION: set[FailureKey] = {("pytest", "tests/test_new.py::test_case")}


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
        rebase_module, "check_base_branch_on_origin", lambda _pd, _b: None
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
    monkeypatch.setattr(
        rebase_module, "get_branch_name_for_logging", lambda _pd: "feature"
    )
    prompt = MagicMock(return_value=("resolved", "sid-1"))
    monkeypatch.setattr(rebase_module, "_prompt_in_session", prompt)
    monkeypatch.setattr(
        rebase_module,
        "_build_conflict_prompt",
        lambda _pd, files: "CONFLICT:" + ",".join(files),
    )
    monkeypatch.setattr(
        rebase_module, "_build_regression_fix_prompt", lambda text: "FIX:" + text
    )

    # Checks + formatter.
    all_checks = MagicMock(return_value=set())
    formatters = MagicMock(return_value=True)
    monkeypatch.setattr(rebase_module, "_run_all_checks", all_checks)
    monkeypatch.setattr(rebase_module, "run_formatters", formatters)

    # Rebase / conflict-loop shim calls.
    rebase_start = MagicMock(return_value=_COMPLETED)
    rebase_continue = MagicMock(return_value=_COMPLETED)
    rebase_skip = MagicMock(return_value=_COMPLETED)
    blob_info = MagicMock(return_value=_blob_info())
    has_staged = MagicMock(return_value=False)
    stage_all = MagicMock(return_value=True)
    commit_all = MagicMock(
        return_value={"success": True, "commit_hash": "abc1234", "error": None}
    )
    resolve_theirs = MagicMock(return_value=_GIT_OK)
    read_stage = MagicMock(
        return_value={**_GIT_OK, "content": "text\n", "is_binary": False}
    )
    monkeypatch.setattr(rebase_module, "rebase_start", rebase_start)
    monkeypatch.setattr(rebase_module, "rebase_continue", rebase_continue)
    monkeypatch.setattr(rebase_module, "rebase_skip", rebase_skip)
    monkeypatch.setattr(rebase_module, "get_conflict_blob_info", blob_info)
    monkeypatch.setattr(rebase_module, "has_staged_changes", has_staged)
    monkeypatch.setattr(rebase_module, "stage_all_changes", stage_all)
    monkeypatch.setattr(rebase_module, "commit_all_changes", commit_all)
    monkeypatch.setattr(rebase_module, "resolve_take_theirs_or_remove", resolve_theirs)
    monkeypatch.setattr(rebase_module, "read_conflict_stage", read_stage)

    # Marker scan + git-state shim calls used by the safety net.
    has_markers = MagicMock(return_value=False)
    mid_rebase = MagicMock(return_value=False)
    success_shape = MagicMock(return_value=True)
    abort = MagicMock(return_value=_GIT_OK)
    reset = MagicMock(return_value=_GIT_OK)
    status = MagicMock(return_value=_CLEAN_STATUS)
    push = MagicMock(return_value={"success": True, "error": None})
    monkeypatch.setattr(rebase_module, "_has_conflict_markers", has_markers)
    monkeypatch.setattr(rebase_module, "is_rebase_in_progress", mid_rebase)
    monkeypatch.setattr(rebase_module, "_rebase_success_shape", success_shape)
    monkeypatch.setattr(rebase_module, "rebase_abort", abort)
    monkeypatch.setattr(rebase_step_module, "reset_hard", reset)
    monkeypatch.setattr(rebase_module, "get_working_tree_status", status)
    monkeypatch.setattr(rebase_module, "git_push", push)

    return SimpleNamespace(
        prompt=prompt,
        all_checks=all_checks,
        formatters=formatters,
        rebase_start=rebase_start,
        rebase_continue=rebase_continue,
        rebase_skip=rebase_skip,
        blob_info=blob_info,
        has_staged=has_staged,
        stage_all=stage_all,
        commit_all=commit_all,
        resolve_theirs=resolve_theirs,
        read_stage=read_stage,
        has_markers=has_markers,
        mid_rebase=mid_rebase,
        success_shape=success_shape,
        abort=abort,
        reset=reset,
        status=status,
        push=push,
        needs=needs,
        fetch=fetch,
    )


def _run(tmp_path: Path, base_branch: str | None = None) -> int:
    return run_rebase_workflow(tmp_path, provider="claude", base_branch=base_branch)


def _start_conflict_loop(patched: SimpleNamespace) -> None:
    """Make the initial rebase stop with a conflict (mid-rebase)."""
    patched.rebase_start.return_value = _STOPPED
    patched.mid_rebase.return_value = True


# --- Guards (unchanged behavior) ---


def test_preflight_error_returns_2_without_llm(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing pre-flight short-circuits to ``2`` and never calls the LLM."""
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: "dirty tree")

    assert _run(tmp_path) == 2
    patched.prompt.assert_not_called()


def test_formatter_config_error_returns_2_without_llm(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A formatter config error in the real pre-flight maps to ``2``, no LLM."""
    monkeypatch.setattr(rebase_module, "_preflight", _REAL_PREFLIGHT)
    monkeypatch.setattr(rebase_module, "get_current_branch_name", lambda _pd: "feature")
    monkeypatch.setattr(
        rebase_module, "get_remote_url", lambda _pd: "https://example.com/r.git"
    )
    monkeypatch.setattr(
        rebase_module,
        "check_formatter_config",
        lambda _pd, warn_legacy_key=False: "No formatter declared: ...",
    )

    assert _run(tmp_path) == 2
    patched.prompt.assert_not_called()
    patched.formatters.assert_not_called()


def test_non_standard_base_without_arg_returns_2(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A base-branch guard error maps to ``2`` and never calls the LLM."""
    monkeypatch.setattr(
        rebase_module,
        "_resolve_base_branch",
        lambda _pd, _arg: (
            None,
            "Base 'develop' was detected from pr, not named in the issue; "
            "add '### Base Branch' to the issue or pass --base-branch",
        ),
    )

    assert _run(tmp_path) == 2
    patched.prompt.assert_not_called()


def test_base_missing_on_origin_returns_2(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A base branch missing on origin maps to ``2`` before the pr_info/ guard."""
    monkeypatch.setattr(
        rebase_module,
        "check_base_branch_on_origin",
        lambda _pd, _b: "Base branch 'epic/x' does not exist on origin",
    )
    pr_info_guard = MagicMock(return_value=None)
    monkeypatch.setattr(rebase_module, "_check_pr_info_absent_on_base", pr_info_guard)

    assert _run(tmp_path) == 2
    pr_info_guard.assert_not_called()
    patched.prompt.assert_not_called()


def test_no_op_when_not_needed_returns_0_without_checks(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """``needs_rebase`` False (up-to-date) short-circuits to ``0`` before checks."""
    patched.needs.return_value = (False, "up-to-date")

    assert _run(tmp_path) == 0
    patched.all_checks.assert_not_called()
    patched.prompt.assert_not_called()


def test_needs_rebase_error_reason_returns_2(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """``needs_rebase`` False with an ``error:`` reason maps to ``2``, not ``0``."""
    patched.needs.return_value = (
        False,
        "error: target branch 'origin/main' not found",
    )

    assert _run(tmp_path) == 2
    patched.prompt.assert_not_called()


def test_pr_info_present_on_base_returns_2(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``pr_info/`` present on the base branch maps to ``2`` before any git write."""
    monkeypatch.setattr(
        rebase_module,
        "_check_pr_info_absent_on_base",
        lambda _pd, _b: "pr_info/ present on origin/main",
    )

    assert _run(tmp_path) == 2
    patched.rebase_start.assert_not_called()


def test_pr_info_listing_failure_returns_2(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed ``list_tree`` on ``origin/<base>`` is a guard error (exit ``2``)."""
    monkeypatch.setattr(
        rebase_module, "_check_pr_info_absent_on_base", _REAL_PR_INFO_GUARD
    )
    monkeypatch.setattr(
        rebase_module,
        "list_tree",
        lambda _pd, _ref, _path: {
            "success": False,
            "error": "git ls-tree failed (exit 128)",
            "returncode": 128,
            "stderr": "fatal: Not a valid object name origin/main",
            "entries": [],
        },
    )

    assert _run(tmp_path) == 2
    patched.rebase_start.assert_not_called()
    patched.all_checks.assert_not_called()


# --- Baseline ---


def test_baseline_check_run_error_returns_2_before_git(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A baseline infrastructure failure exits ``2`` with no git mutation."""
    patched.all_checks.side_effect = CheckRunError("pytest: failed to run")

    assert _run(tmp_path) == 2
    patched.rebase_start.assert_not_called()
    patched.prompt.assert_not_called()


def test_pre_existing_baseline_failures_do_not_block(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Identical failures before and after the rebase are not regressions."""
    patched.all_checks.side_effect = [set(_REGRESSION), set(_REGRESSION)]

    assert _run(tmp_path) == 0
    patched.prompt.assert_not_called()
    patched.push.assert_called_once()


# --- Fast path ---


def test_fast_path_clean_rebase_pushes_without_llm(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Clean rebase + empty regression set → push, exit ``0``, zero LLM calls."""
    assert _run(tmp_path) == 0
    patched.rebase_start.assert_called_once_with(tmp_path, "origin/main")
    patched.push.assert_called_once()
    _args, kwargs = patched.push.call_args
    assert kwargs.get("force_with_lease") is True
    patched.prompt.assert_not_called()
    patched.reset.assert_not_called()


# --- Conflict loop ---


def test_pr_info_only_conflict_auto_resolved_without_llm(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A ``pr_info/``-only conflict is auto-resolved; the LLM is never called."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("pr_info/TASK_TRACKER.md")

    assert _run(tmp_path) == 0
    patched.resolve_theirs.assert_called_once_with(tmp_path, "pr_info/TASK_TRACKER.md")
    patched.prompt.assert_not_called()
    patched.stage_all.assert_called_once_with(tmp_path)
    patched.rebase_continue.assert_called_once_with(tmp_path)


def test_pr_info_resolution_failure_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A failed ``pr_info/`` auto-resolution aborts with ``1``."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("pr_info/TASK_TRACKER.md")
    patched.resolve_theirs.return_value = _GIT_FAIL

    assert _run(tmp_path) == 1
    patched.push.assert_not_called()
    patched.abort.assert_called_once()


def test_mixed_conflict_calls_llm_with_non_pr_info_files(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Mixed conflict: ``pr_info/`` auto-resolves, the rest goes to the LLM."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("pr_info/x.md", "src/a.py")

    assert _run(tmp_path) == 0
    patched.resolve_theirs.assert_called_once_with(tmp_path, "pr_info/x.md")
    patched.prompt.assert_called_once()
    assert patched.prompt.call_args.args[0] == "CONFLICT:src/a.py"
    patched.push.assert_called_once()


def test_markers_remaining_after_llm_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Conflict markers left behind by the LLM abort with ``1`` (rule 3)."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.has_markers.return_value = True

    assert _run(tmp_path) == 1
    patched.prompt.assert_called_once()
    patched.push.assert_not_called()
    patched.abort.assert_called_once()


def test_binary_conflict_returns_1_without_llm(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A binary conflict aborts with ``1`` before any LLM call (rule 2)."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info(
        "assets/img.png", binary=("assets/img.png",)
    )

    assert _run(tmp_path) == 1
    patched.prompt.assert_not_called()
    patched.abort.assert_called_once()


def test_conflict_blob_info_failure_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Unreadable conflict state fails closed: exit ``1``, no LLM, no continue."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = {
        "success": False,
        "error": "git ls-files -u failed (exit 128)",
        "returncode": 128,
        "stderr": "fatal",
        "entries": [],
    }

    assert _run(tmp_path) == 1
    patched.prompt.assert_not_called()
    patched.rebase_continue.assert_not_called()
    patched.abort.assert_called_once()


def test_same_file_three_stops_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """The same file conflicting at 3 stops aborts with ``1`` (rule 4)."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.rebase_continue.return_value = _STOPPED  # every continue stops again

    assert _run(tmp_path) == 1
    assert patched.prompt.call_count == 2  # the third stop aborts before the LLM
    patched.push.assert_not_called()


def test_rebase_error_status_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A rebase ``error`` status (not left in progress) aborts with ``1``."""
    patched.rebase_start.return_value = _REBASE_ERROR

    assert _run(tmp_path) == 1
    patched.blob_info.assert_not_called()
    patched.prompt.assert_not_called()
    patched.push.assert_not_called()


def test_empty_commit_stop_skips_and_succeeds(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A redundant (empty) commit is skipped via ``rebase_skip``."""
    _start_conflict_loop(patched)
    patched.has_staged.return_value = False

    assert _run(tmp_path) == 0
    patched.rebase_skip.assert_called_once_with(tmp_path)
    patched.prompt.assert_not_called()
    patched.push.assert_called_once()


def test_non_conflict_stop_with_staged_changes_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """No conflicted files but staged changes aborts (no skip)."""
    _start_conflict_loop(patched)
    patched.has_staged.return_value = True

    assert _run(tmp_path) == 1
    patched.rebase_skip.assert_not_called()
    patched.push.assert_not_called()


# --- Regression-fix loop ---


def test_regression_fixed_on_first_attempt(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A regression fixed on attempt 1 commits the fix and pushes (exit 0)."""
    patched.all_checks.side_effect = [set(), set(_REGRESSION), set()]

    assert _run(tmp_path) == 0
    patched.prompt.assert_called_once()
    assert patched.prompt.call_args.args[0].startswith("FIX:")
    patched.formatters.assert_called_once_with(tmp_path)
    patched.commit_all.assert_called_once_with(
        "fix: resolve regressions from rebase onto origin/main", tmp_path
    )
    patched.push.assert_called_once()


def test_regression_fix_formats_through_run_formatters(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fix loop formats via the gated ``run_formatters``, not the wrapper."""
    monkeypatch.setattr(rebase_module, "run_formatters", commit_module.run_formatters)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
    )
    wrapper = MagicMock(return_value={})
    monkeypatch.setattr(commit_module, "run_format_code", wrapper)
    patched.all_checks.side_effect = [set(), set(_REGRESSION), set()]

    assert _run(tmp_path) == 0
    assert not hasattr(rebase_module, "run_format_code")
    wrapper.assert_not_called()


def test_identical_regression_text_stalls_and_resets(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Identical failure text on the re-check trips the stall guard (exit 1)."""
    patched.all_checks.side_effect = [set(), set(_REGRESSION), set(_REGRESSION)]

    assert _run(tmp_path) == 1
    patched.prompt.assert_called_once()  # stall guard blocks attempt 2
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_regressions_after_two_attempts_reset_and_return_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Still-failing regressions after 2 attempts reset to ``pre_sha`` (exit 1)."""
    other: set[FailureKey] = {("mypy", "src/m.py", "arg-type", "bad")}
    patched.all_checks.side_effect = [
        set(),
        set(_REGRESSION),
        other,
        set(_REGRESSION),
    ]

    assert _run(tmp_path) == 1
    assert patched.prompt.call_count == 2
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_verification_check_run_error_resets_and_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A verification infrastructure failure resets to ``pre_sha`` (exit 1)."""
    patched.all_checks.side_effect = [set(), CheckRunError("pylint: failed to run")]

    assert _run(tmp_path) == 1
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_llm_timeout_during_fix_resets_and_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """An LLM timeout after the rebase completed resets to ``pre_sha`` (exit 1)."""
    patched.all_checks.side_effect = [set(), set(_REGRESSION)]
    patched.prompt.side_effect = LLMTimeoutError("no output for 600s")

    assert _run(tmp_path) == 1
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_llm_timeout_mid_rebase_aborts_without_reset(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """An LLM timeout at a conflict stop leaves the abort to the finally net."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.prompt.side_effect = LLMTimeoutError("no output for 600s")

    assert _run(tmp_path) == 1
    patched.abort.assert_called_once()
    patched.reset.assert_not_called()


# --- Corroboration gate + push ---


def test_corroboration_gate_failure_resets_and_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Git state not corroborating success resets to ``pre_sha`` (exit 1)."""
    patched.success_shape.return_value = False

    assert _run(tmp_path) == 1
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_push_rejected_resets_and_returns_2(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A rejected force-push restores ``pre_sha`` and maps to ``2``."""
    patched.push.return_value = {"success": False, "error": "stale info"}

    assert _run(tmp_path) == 2
    patched.reset.assert_called_once_with(tmp_path, "presha")


# --- Safety net: reset / abort / unknown rebase state ---


def test_reset_failure_reported_as_failed(
    patched: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed ``reset_hard`` says FAILED in the abort message and logs an error."""
    patched.success_shape.return_value = False
    patched.reset.return_value = _GIT_FAIL

    with caplog.at_level(OUTPUT, logger="mcp_coder.workflows.rebase"):
        assert _run(tmp_path) == 1

    output = [r.getMessage() for r in caplog.records if r.levelno == OUTPUT]
    aborted = [m for m in output if m.startswith("Aborted:")]
    assert len(aborted) == 1
    assert "FAILED" in aborted[0]
    assert "pre-rebase state restored" not in aborted[0]
    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any("reset --hard presha failed" in m for m in errors)


def test_reset_success_reported_as_restored(
    patched: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A successful reset keeps the ``pre-rebase state restored`` phrase."""
    patched.push.return_value = {"success": False, "error": "stale info"}

    with caplog.at_level(OUTPUT, logger="mcp_coder.workflows.rebase"):
        assert _run(tmp_path) == 2

    output = [r.getMessage() for r in caplog.records if r.levelno == OUTPUT]
    assert "Aborted: force-push rejected; pre-rebase state restored" in output


def test_unknown_rebase_state_in_except_skips_reset_and_abort(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """``is_rebase_in_progress`` raising in except/finally: exit 1, no reset/abort."""
    patched.all_checks.side_effect = [set(), set(_REGRESSION)]
    patched.prompt.side_effect = LLMTimeoutError("no output for 600s")
    patched.mid_rebase.side_effect = ValueError("not a git repository")

    assert _run(tmp_path) == 1
    patched.reset.assert_not_called()
    patched.abort.assert_not_called()


def test_finally_does_not_abort_when_not_mid_rebase(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """The finally net aborts only when ``is_rebase_in_progress`` is True."""
    patched.success_shape.return_value = False

    assert _run(tmp_path) == 1
    patched.abort.assert_not_called()


def test_finally_aborts_when_mid_rebase(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A rebase left in progress is aborted by the finally net."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info(
        "assets/img.png", binary=("assets/img.png",)
    )

    assert _run(tmp_path) == 1
    patched.abort.assert_called_once_with(tmp_path)


def test_abort_failure_is_logged(
    patched: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed ``rebase_abort`` in the finally net is logged at error level."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info(
        "assets/img.png", binary=("assets/img.png",)
    )
    patched.abort.return_value = {**_GIT_FAIL, "stderr": "abort exploded"}

    with caplog.at_level(logging.ERROR, logger="mcp_coder.workflows.rebase"):
        assert _run(tmp_path) == 1

    errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any("rebase --abort failed: abort exploded" in m for m in errors)


def test_success_shape_raise_resets_to_pre_sha(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Completed rebase, then the state probe raises: shape False, reset, exit 1."""
    monkeypatch.setattr(rebase_module, "_rebase_success_shape", _REAL_SUCCESS_SHAPE)
    patched.mid_rebase.side_effect = ValueError("not a git repository")

    assert _run(tmp_path) == 1
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()
    patched.abort.assert_not_called()


# --- _rebase_success_shape (shim-mocked) ---


def test_success_shape_false_when_status_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed ``get_working_tree_status`` is never clean (fail-closed)."""
    monkeypatch.setattr(rebase_module, "is_rebase_in_progress", lambda _pd: False)
    monkeypatch.setattr(
        rebase_module, "get_working_tree_status", lambda _pd: _FAILED_STATUS
    )
    monkeypatch.setattr(rebase_module, "get_latest_commit_sha", lambda _pd: "newsha")

    assert _REAL_SUCCESS_SHAPE(tmp_path, "presha") is False


def test_success_shape_false_when_state_probe_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """An ``is_rebase_in_progress`` raise is logged and reads as not-successful."""

    def _raise(_pd: Path) -> bool:
        raise ValueError("not a git repository")

    monkeypatch.setattr(rebase_module, "is_rebase_in_progress", _raise)
    monkeypatch.setattr(
        rebase_module, "get_working_tree_status", lambda _pd: _CLEAN_STATUS
    )
    monkeypatch.setattr(rebase_module, "get_latest_commit_sha", lambda _pd: "newsha")

    with caplog.at_level(logging.ERROR, logger="mcp_coder.workflows.rebase"):
        assert _REAL_SUCCESS_SHAPE(tmp_path, "presha") is False
    assert any(
        "Could not determine rebase state" in r.getMessage() for r in caplog.records
    )


# --- Session threading ---


def test_session_id_threads_between_llm_calls(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """The session id from the first LLM response resumes the second call."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.rebase_continue.side_effect = [_STOPPED, _COMPLETED]
    patched.prompt.side_effect = [("r1", "sid-1"), ("r2", "sid-2")]

    assert _run(tmp_path) == 0
    assert patched.prompt.call_count == 2
    assert patched.prompt.call_args_list[0].args[1] is None
    assert patched.prompt.call_args_list[1].args[1] == "sid-1"
    assert patched.prompt.call_args_list[0].kwargs["step_name"] == "conflict_1"
    assert patched.prompt.call_args_list[1].kwargs["step_name"] == "conflict_2"


# --- OUTPUT logging ---


def test_output_logging_start_and_result(
    patched: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A successful run logs the start and the pushed result at OUTPUT level."""
    with caplog.at_level(OUTPUT, logger="mcp_coder.workflows.rebase"):
        assert _run(tmp_path) == 0

    messages = [r.getMessage() for r in caplog.records if r.levelno == OUTPUT]
    assert any("Starting automated rebase" in m for m in messages)
    assert any("force-pushed" in m for m in messages)


def test_no_op_logs_nothing_to_do_at_output(
    patched: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The up-to-date no-op logs its result at OUTPUT level (user-visible)."""
    patched.needs.return_value = (False, "up-to-date")
    with caplog.at_level(OUTPUT, logger="mcp_coder.workflows.rebase"):
        assert _run(tmp_path) == 0

    messages = [r.getMessage() for r in caplog.records if r.levelno == OUTPUT]
    assert any("nothing to do" in m for m in messages)
