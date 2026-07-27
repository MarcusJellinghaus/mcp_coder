"""Fully-mocked tests for the ``run_rebase_workflow`` orchestrator.

Python drives every git operation and every check; the LLM is consulted only
for conflict resolution and regression fixes. Every exit-code path is
exercised without touching a real repository, network, or LLM: each test
patches the orchestrator's collaborators on ``mcp_coder.workflows.rebase``
(git helpers, check runner, LLM session helper, push) and asserts the exit
code plus the safety-net side effects (force-push, reset, abort-in-finally)
and OUTPUT-level progress logging.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import _GitResult, run_rebase_workflow
from mcp_coder.workflows.rebase_checks import CheckRunError, FailureKey

_OK = _GitResult(0, "", "")
_FAIL = _GitResult(1, "", "boom")

_REGRESSION: set[FailureKey] = {("pytest", "tests/test_new.py::test_case")}


@pytest.fixture
def patched(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator to a benign happy-path default.

    Returns a namespace of the recordable mocks so individual tests can tweak
    return values / side effects and assert call arguments. ``set_git`` queues
    per-argv results for the ``_run_git`` mock (last queued result repeats).
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
    format_code = MagicMock(return_value={})
    monkeypatch.setattr(rebase_module, "_run_all_checks", all_checks)
    monkeypatch.setattr(rebase_module, "run_format_code", format_code)

    # Raw git calls (initial rebase, --cached probe, --skip, add, commit).
    git_calls: list[tuple[str, ...]] = []
    git_results: dict[tuple[str, ...], list[_GitResult]] = {}

    def fake_run_git(_pd: Path, *args: str) -> _GitResult:
        git_calls.append(args)
        queued = git_results.get(args)
        if queued:
            return queued.pop(0) if len(queued) > 1 else queued[0]
        return _OK

    run_git = MagicMock(side_effect=fake_run_git)
    monkeypatch.setattr(rebase_module, "_run_git", run_git)

    def set_git(args: tuple[str, ...], *results: _GitResult) -> None:
        git_results[args] = list(results)

    # Conflict-loop helpers + git-state helpers used by the safety net.
    conflicted = MagicMock(return_value=[])
    binary = MagicMock(return_value=None)
    resolve_pr_info = MagicMock(return_value=True)
    has_markers = MagicMock(return_value=False)
    stage_continue = MagicMock(return_value=_OK)
    mid_rebase = MagicMock(return_value=False)
    success_shape = MagicMock(return_value=True)
    abort = MagicMock()
    reset = MagicMock()
    push = MagicMock(return_value={"success": True, "error": None})
    monkeypatch.setattr(rebase_module, "_conflicted_files", conflicted)
    monkeypatch.setattr(rebase_module, "_binary_conflict", binary)
    monkeypatch.setattr(rebase_module, "_resolve_pr_info_conflict", resolve_pr_info)
    monkeypatch.setattr(rebase_module, "_has_conflict_markers", has_markers)
    monkeypatch.setattr(rebase_module, "_stage_all_and_continue", stage_continue)
    monkeypatch.setattr(rebase_module, "_is_rebase_in_progress", mid_rebase)
    monkeypatch.setattr(rebase_module, "_rebase_success_shape", success_shape)
    monkeypatch.setattr(rebase_module, "_abort_rebase", abort)
    monkeypatch.setattr(rebase_module, "_reset_hard", reset)
    monkeypatch.setattr(rebase_module, "git_push", push)

    return SimpleNamespace(
        prompt=prompt,
        all_checks=all_checks,
        format_code=format_code,
        run_git=run_git,
        git_calls=git_calls,
        set_git=set_git,
        conflicted=conflicted,
        binary=binary,
        resolve_pr_info=resolve_pr_info,
        has_markers=has_markers,
        stage_continue=stage_continue,
        mid_rebase=mid_rebase,
        success_shape=success_shape,
        abort=abort,
        reset=reset,
        push=push,
        needs=needs,
        fetch=fetch,
    )


def _run(tmp_path: Path, base_branch: str | None = None) -> int:
    return run_rebase_workflow(tmp_path, provider="claude", base_branch=base_branch)


def _start_conflict_loop(patched: SimpleNamespace) -> None:
    """Make the initial ``git rebase`` stop with a conflict (mid-rebase)."""
    patched.set_git(("rebase", "origin/main"), _FAIL)
    patched.mid_rebase.return_value = True


# --- Guards (unchanged behavior) ---


def test_preflight_error_returns_2_without_llm(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing pre-flight short-circuits to ``2`` and never calls the LLM."""
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: "dirty tree")

    assert _run(tmp_path) == 2
    patched.prompt.assert_not_called()


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
    patched.run_git.assert_not_called()


# --- Baseline ---


def test_baseline_check_run_error_returns_2_before_git(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A baseline infrastructure failure exits ``2`` with no git mutation."""
    patched.all_checks.side_effect = CheckRunError("pytest: failed to run")

    assert _run(tmp_path) == 2
    patched.run_git.assert_not_called()
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
    assert ("rebase", "origin/main") in patched.git_calls
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
    patched.conflicted.return_value = ["pr_info/TASK_TRACKER.md"]

    assert _run(tmp_path) == 0
    patched.resolve_pr_info.assert_called_once_with(tmp_path, "pr_info/TASK_TRACKER.md")
    patched.prompt.assert_not_called()
    patched.stage_continue.assert_called_once()


def test_pr_info_resolution_failure_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A failed ``pr_info/`` auto-resolution aborts with ``1``."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = ["pr_info/TASK_TRACKER.md"]
    patched.resolve_pr_info.return_value = False

    assert _run(tmp_path) == 1
    patched.push.assert_not_called()
    patched.abort.assert_called_once()


def test_mixed_conflict_calls_llm_with_non_pr_info_files(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Mixed conflict: ``pr_info/`` auto-resolves, the rest goes to the LLM."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = ["pr_info/x.md", "src/a.py"]

    assert _run(tmp_path) == 0
    patched.resolve_pr_info.assert_called_once_with(tmp_path, "pr_info/x.md")
    patched.prompt.assert_called_once()
    assert patched.prompt.call_args.args[0] == "CONFLICT:src/a.py"
    patched.push.assert_called_once()


def test_markers_remaining_after_llm_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Conflict markers left behind by the LLM abort with ``1`` (rule 3)."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = ["src/a.py"]
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
    patched.conflicted.return_value = ["assets/img.png"]
    patched.binary.return_value = "assets/img.png"

    assert _run(tmp_path) == 1
    patched.prompt.assert_not_called()
    patched.abort.assert_called_once()


def test_same_file_three_stops_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """The same file conflicting at 3 stops aborts with ``1`` (rule 4)."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = ["src/a.py"]
    patched.stage_continue.return_value = _FAIL  # every continue hits a new stop

    assert _run(tmp_path) == 1
    assert patched.prompt.call_count == 2  # the third stop aborts before the LLM
    patched.push.assert_not_called()


def test_unexpected_rebase_error_not_mid_rebase_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A failed ``git rebase`` with no rebase in progress aborts with ``1``."""
    patched.set_git(("rebase", "origin/main"), _FAIL)
    patched.mid_rebase.return_value = False

    assert _run(tmp_path) == 1
    patched.prompt.assert_not_called()
    patched.push.assert_not_called()


def test_empty_commit_stop_skips_and_succeeds(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A redundant (empty) commit is skipped via ``git rebase --skip``."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = []
    patched.set_git(("diff", "--cached", "--quiet"), _OK)
    patched.set_git(("rebase", "--skip"), _OK)

    assert _run(tmp_path) == 0
    assert ("rebase", "--skip") in patched.git_calls
    patched.prompt.assert_not_called()
    patched.push.assert_called_once()


def test_non_conflict_failure_with_dirty_index_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """No conflicted files but a dirty staged diff aborts (no ``--skip``)."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = []
    patched.set_git(("diff", "--cached", "--quiet"), _FAIL)

    assert _run(tmp_path) == 1
    assert ("rebase", "--skip") not in patched.git_calls
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
    patched.format_code.assert_called_once()
    assert (
        "commit",
        "-m",
        "fix: resolve regressions from rebase onto origin/main",
    ) in patched.git_calls
    patched.push.assert_called_once()


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
    patched.conflicted.return_value = ["src/a.py"]
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


# --- Session threading ---


def test_session_id_threads_between_llm_calls(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """The session id from the first LLM response resumes the second call."""
    _start_conflict_loop(patched)
    patched.conflicted.return_value = ["src/a.py"]
    patched.stage_continue.side_effect = [_FAIL, _OK]
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
