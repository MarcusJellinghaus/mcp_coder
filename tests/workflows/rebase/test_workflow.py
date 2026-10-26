"""Fully-mocked tests for the ``run_rebase_workflow`` orchestrator.

Python drives every git operation and every check; the LLM is consulted only
for conflict resolution and regression fixes. Every exit-code path is
exercised without touching a real repository, network, or LLM: each test
patches the orchestrator's collaborators on ``mcp_coder.workflows.rebase``
(git helpers, check runner, LLM session helper, push) and asserts the exit
code plus the safety-net side effects (force-push, reset, abort-in-finally)
and OUTPUT-level progress logging.

The shared ``patched`` fixture and shim-result constants live in
``conftest.py``; the regression-fix loop and the safety net are covered in
``test_workflow_regression.py`` and ``test_workflow_safety_net.py``.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase_checks import CheckRunError
from tests.workflows.rebase.conftest import (
    _COMPLETED,
    _GIT_FAIL,
    _REAL_PR_INFO_GUARD,
    _REAL_PREFLIGHT,
    _REBASE_ERROR,
    _REGRESSION,
    _STOPPED,
    _blob_info,
    _run,
    _start_conflict_loop,
)

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
