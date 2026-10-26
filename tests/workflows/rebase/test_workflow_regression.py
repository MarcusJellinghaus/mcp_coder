"""Fully-mocked ``run_rebase_workflow`` tests: regression-fix loop and push.

Covers the post-rebase regression-fix loop (stall guard, attempt cap, LLM
timeout) and the corroboration gate before the force-push.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.workflow_steps import commit as commit_module
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase_checks import CheckRunError, FailureKey
from tests.workflows.rebase.conftest import (
    _REGRESSION,
    _blob_info,
    _run,
    _start_conflict_loop,
)

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
