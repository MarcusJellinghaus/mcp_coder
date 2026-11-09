"""Fully-mocked ``run_rebase_workflow`` tests: regression-fix loop and push.

Covers the post-rebase regression-fix loop (stall guard, attempt cap, LLM
timeout) and the corroboration gate before the force-push.
"""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.workflow_steps import commit as commit_module
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import RebaseRunResult
from mcp_coder.workflows.rebase_checks import CheckRunError, FailureKey
from tests.workflows.rebase.conftest import (
    _REGRESSION,
    _blob_info,
    _checked,
    _run,
    _start_conflict_loop,
)

# --- Regression-fix loop ---


def test_regression_fixed_on_first_attempt(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A regression fixed on attempt 1 commits the fix and pushes (exit 0)."""
    patched.all_checks.side_effect = [_checked(), _checked(*_REGRESSION), _checked()]

    assert _run(tmp_path).exit_code == 0
    patched.prompt.assert_called_once()
    assert patched.prompt.call_args.args[0].startswith("FIX:")
    patched.formatters.assert_called_once_with(tmp_path)
    patched.commit_all.assert_called_once_with(
        "fix: resolve regressions from rebase onto origin/main", tmp_path
    )
    patched.push.assert_called_once()


def test_automated_reaches_every_check_run_and_fix_prompt(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``automated`` reaches baseline, verification, re-check and the filter text."""
    fix_prompt = MagicMock(return_value="FIX:")
    filter_text = MagicMock(return_value="FILTER")
    monkeypatch.setattr(rebase_module, "_build_regression_fix_prompt", fix_prompt)
    monkeypatch.setattr(rebase_module, "_marker_filter_text", filter_text)
    patched.all_checks.side_effect = [_checked(), _checked(*_REGRESSION), _checked()]

    result = rebase_module.run_rebase_workflow(
        tmp_path, provider="claude", automated=True
    )

    assert result.exit_code == 0
    assert [c.args for c in patched.all_checks.call_args_list] == [(tmp_path, True)] * 3
    filter_text.assert_called_once_with(tmp_path, True)
    assert fix_prompt.call_args.args[1] == "FILTER"


def test_not_automated_runs_rebase_binding(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Without ``automated`` (the CLI), every check run gets ``False``."""
    assert _run(tmp_path).exit_code == 0
    assert patched.all_checks.call_count == 2
    assert all(c.args[1] is False for c in patched.all_checks.call_args_list)


def test_regression_fix_formats_through_run_formatters(
    patched: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fix loop formats via the gated ``run_formatters``, not the wrapper."""
    monkeypatch.setattr(rebase_module, "run_formatters", commit_module.run_formatters)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
    )
    wrapper = MagicMock(return_value=[])
    monkeypatch.setattr(commit_module, "run_binding", wrapper)
    patched.all_checks.side_effect = [_checked(), _checked(*_REGRESSION), _checked()]

    assert _run(tmp_path).exit_code == 0
    assert not hasattr(rebase_module, "run_format_code")
    wrapper.assert_not_called()


def test_identical_regression_text_stalls_and_resets(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Identical failure text on the re-check trips the stall guard (exit 1)."""
    patched.all_checks.side_effect = [
        _checked(),
        _checked(*_REGRESSION),
        _checked(*_REGRESSION),
    ]

    assert _run(tmp_path).exit_code == 1
    patched.prompt.assert_called_once()  # stall guard blocks attempt 2
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_regressions_after_two_attempts_reset_and_return_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Still-failing regressions after 2 attempts reset to ``pre_sha`` (exit 1)."""
    other: set[FailureKey] = {"check: src/m.py|arg-type|bad"}
    patched.all_checks.side_effect = [
        _checked(),
        _checked(*_REGRESSION),
        _checked(*other),
        _checked(*_REGRESSION),
    ]

    assert _run(tmp_path).exit_code == 1
    assert patched.prompt.call_count == 2
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_verification_check_run_error_resets_and_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A verification infrastructure failure resets to ``pre_sha`` (exit 1)."""
    patched.all_checks.side_effect = [
        _checked(),
        CheckRunError("pylint: failed to run"),
    ]

    result = _run(tmp_path)

    assert result.exit_code == 1
    assert "pylint: failed to run" in result.reason
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_llm_timeout_during_fix_resets_and_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """An LLM timeout after the rebase completed resets to ``pre_sha`` (exit 1)."""
    patched.all_checks.side_effect = [_checked(), _checked(*_REGRESSION)]
    patched.prompt.side_effect = LLMTimeoutError("no output for 600s")

    assert _run(tmp_path).exit_code == 1
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_llm_timeout_mid_rebase_aborts_without_reset(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """An LLM timeout at a conflict stop leaves the abort to the finally net."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.prompt.side_effect = LLMTimeoutError("no output for 600s")

    assert _run(tmp_path).exit_code == 1
    patched.abort.assert_called_once()
    patched.reset.assert_not_called()


# --- Corroboration gate + push ---


def test_corroboration_gate_failure_resets_and_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Git state not corroborating success resets to ``pre_sha`` (exit 1)."""
    patched.success_shape.return_value = False

    assert _run(tmp_path).exit_code == 1
    patched.reset.assert_called_once_with(tmp_path, "presha")
    patched.push.assert_not_called()


def test_push_rejected_resets_and_returns_2(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A rejected force-push restores ``pre_sha`` and maps to ``2``."""
    patched.push.return_value = {"success": False, "error": "stale info"}

    assert _run(tmp_path).exit_code == 2
    patched.reset.assert_called_once_with(tmp_path, "presha")


# --- RebaseRunResult: reason / push_rejected ---


def _preflight_fails(_ns: SimpleNamespace, mp: pytest.MonkeyPatch) -> None:
    mp.setattr(rebase_module, "_preflight", lambda _pd: "dirty tree")


def _baseline_fails(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    ns.all_checks.side_effect = CheckRunError("pytest: failed to run")


def _markers_remain(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    _start_conflict_loop(ns)
    ns.blob_info.return_value = _blob_info("src/a.py")
    ns.has_markers.return_value = True


def _binary_conflict(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    _start_conflict_loop(ns)
    ns.blob_info.return_value = _blob_info("img.png", binary=("img.png",))


def _unfixed_regressions(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    ns.all_checks.side_effect = [
        _checked(),
        _checked(*_REGRESSION),
        _checked(*_REGRESSION),
    ]


def _not_corroborated(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    ns.success_shape.return_value = False


def _llm_timeout(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    _start_conflict_loop(ns)
    ns.blob_info.return_value = _blob_info("src/a.py")
    ns.prompt.side_effect = LLMTimeoutError("")


def _push_rejected(ns: SimpleNamespace, _mp: pytest.MonkeyPatch) -> None:
    ns.push.return_value = {"success": False, "error": "stale info"}


@pytest.mark.parametrize(
    ("setup", "exit_code", "reason_part", "push_rejected"),
    [
        (_preflight_fails, 2, "Pre-flight failed: dirty tree", False),
        (_baseline_fails, 2, "Baseline checks failed to run", False),
        (_markers_remain, 1, "conflict markers remain in src/a.py", False),
        (_binary_conflict, 1, "binary conflict in img.png", False),
        (_unfixed_regressions, 1, "1 unfixed regression(s)", False),
        (_not_corroborated, 1, "does not corroborate", False),
        (_llm_timeout, 1, "LLMTimeoutError", False),
        (_push_rejected, 2, "force-push rejected", True),
    ],
)
def test_result_reason_and_push_rejected(  # pylint: disable=too-many-arguments
    patched: SimpleNamespace,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    setup: Callable[[SimpleNamespace, pytest.MonkeyPatch], None],
    exit_code: int,
    reason_part: str,
    push_rejected: bool,
) -> None:
    """Each abort path carries a non-empty reason; only push rejection flags it."""
    setup(patched, monkeypatch)

    result = _run(tmp_path)

    assert result.exit_code == exit_code
    assert result.reason
    assert reason_part in result.reason
    assert result.push_rejected is push_rejected


def test_success_result_has_reason_and_no_push_rejection(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """A pushed rebase returns exit 0 with a success reason."""
    result = _run(tmp_path)

    assert result == RebaseRunResult(0, "Rebased and force-pushed onto origin/main")
