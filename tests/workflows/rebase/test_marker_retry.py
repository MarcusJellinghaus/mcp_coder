"""Tests for the one-shot marker retry after each conflict-resolution prompt.

When conflict markers remain after the LLM's conflict edit, the orchestrator
resumes the same session once with a marker-retry prompt before aborting.
"""

from pathlib import Path
from types import SimpleNamespace

from mcp_coder.workflows import rebase as rebase_module
from tests.workflows.rebase.conftest import (
    _COMPLETED,
    _STOPPED,
    _blob_info,
    _run,
    _start_conflict_loop,
)


def _step_names(patched: SimpleNamespace) -> list[str]:
    return [c.kwargs["step_name"] for c in patched.prompt.call_args_list]


def test_markers_fixed_by_retry_completes(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Markers cleared by the retry let the loop continue to a pushed rebase."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.has_markers.side_effect = [True, False]

    assert _run(tmp_path).exit_code == 0
    assert _step_names(patched) == ["conflict_1", "conflict_1_retry"]
    retry_prompt = patched.prompt.call_args_list[1].args[0]
    assert retry_prompt == rebase_module._MARKER_RETRY_PROMPT.format(files="src/a.py")
    patched.push.assert_called_once()


def test_markers_survive_retry_returns_1(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Markers surviving the retry abort with ``1`` and name the file."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.has_markers.return_value = True

    result = _run(tmp_path)

    assert result.exit_code == 1
    assert "conflict markers remain in src/a.py" in result.reason
    assert _step_names(patched) == ["conflict_1", "conflict_1_retry"]
    patched.push.assert_not_called()


def test_retry_only_rechecks_unresolved_files(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """The retry names only the files that still carry markers."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py", "src/b.py")
    # First scan: a clean, b marked. Retry re-scan: b clean.
    patched.has_markers.side_effect = [False, True, False]

    assert _run(tmp_path).exit_code == 0
    retry_prompt = patched.prompt.call_args_list[1].args[0]
    assert retry_prompt == rebase_module._MARKER_RETRY_PROMPT.format(files="src/b.py")


def test_one_retry_per_stop_resumes_session(
    patched: SimpleNamespace, tmp_path: Path
) -> None:
    """Two stops with markers → two retries, each resuming the current session."""
    _start_conflict_loop(patched)
    patched.rebase_continue.side_effect = [_STOPPED, _COMPLETED]
    patched.blob_info.return_value = _blob_info("src/a.py")
    patched.has_markers.side_effect = [True, False, True, False]
    patched.prompt.side_effect = [
        ("ok", "sid-1"),
        ("ok", "sid-2"),
        ("ok", "sid-3"),
        ("ok", "sid-4"),
    ]

    assert _run(tmp_path).exit_code == 0
    assert _step_names(patched) == [
        "conflict_1",
        "conflict_1_retry",
        "conflict_2",
        "conflict_2_retry",
    ]
    session_args = [c.args[1] for c in patched.prompt.call_args_list]
    assert session_args == [None, "sid-1", "sid-2", "sid-3"]


def test_no_markers_no_retry(patched: SimpleNamespace, tmp_path: Path) -> None:
    """No markers after the conflict edit → no retry prompt is sent."""
    _start_conflict_loop(patched)
    patched.blob_info.return_value = _blob_info("src/a.py")

    assert _run(tmp_path).exit_code == 0
    assert _step_names(patched) == ["conflict_1"]
