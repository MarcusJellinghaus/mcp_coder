"""Fully-mocked ``run_rebase_workflow`` tests: reset / abort safety net.

Covers reset and abort reporting, the unknown-rebase-state paths, and
``_rebase_success_shape`` against mocked shim results.
"""

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows import rebase as rebase_module
from tests.workflows.rebase.conftest import (
    _CLEAN_STATUS,
    _FAILED_STATUS,
    _GIT_FAIL,
    _REAL_SUCCESS_SHAPE,
    _REGRESSION,
    _blob_info,
    _run,
    _start_conflict_loop,
)

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
