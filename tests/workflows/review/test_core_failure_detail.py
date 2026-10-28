"""The failure comment and banner name the exception that stopped the review.

Drives :func:`run_review_workflow` against ``REVIEW_PLAN`` with a mocked
``prompt_llm`` raising at the fresh reviewer, the supervisor and the fix-task
reviewer, and checks what ``_fail`` hands to ``handle_workflow_failure``.
"""

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_coder.utils.subprocess_runner import CalledProcessError
from mcp_coder.workflows.review import handoff
from mcp_coder.workflows.review.config import REVIEW_PLAN
from tests.workflows.review.conftest import _TASKS, _resp, _reviewer, _run


def _comment(env: SimpleNamespace) -> str:
    """Return the failure comment body passed to ``handle_workflow_failure``."""
    body: str = env.handle_workflow_failure.call_args.args[1]
    return body


def _error_lines(comment: str) -> list[str]:
    """Return the comment lines carrying the ``**Error:**`` field."""
    return [line for line in comment.splitlines() if line.startswith("**Error:** ")]


def test_reviewer_called_process_error_shows_stderr(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A CLI failure shows its stderr, without the stream-file path, capped."""
    env.prompt_llm.side_effect = CalledProcessError(
        1,
        "claude",
        stderr="529 Overloaded " + "x" * 400 + " Stream file: /agent/s.log",
    )

    assert _run(tmp_path, config=REVIEW_PLAN) == 1

    comment = _comment(env)
    assert "CalledProcessError: 529 Overloaded" in comment
    assert "Stream file" not in comment
    assert "/agent/s.log" not in comment
    (line,) = _error_lines(comment)
    value = line.removeprefix("**Error:** ")
    assert len(value) <= 300
    assert value.endswith("…")
    assert "529 Overloaded" in env.handle_workflow_failure.call_args.args[0].message


def test_reviewer_multiline_stderr_stays_on_one_line(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Line breaks in stderr collapse so the Error field stays one line."""
    env.prompt_llm.side_effect = CalledProcessError(
        1,
        "claude",
        stderr="first line\nsecond line\r\n"
        + "y" * 400
        + "\nStream file: /agent/s.log",
    )

    assert _run(tmp_path, config=REVIEW_PLAN) == 1

    comment = _comment(env)
    (line,) = _error_lines(comment)
    value = line.removeprefix("**Error:** ")
    assert "first line second line" in value
    assert len(value) <= 300
    assert "Stream file" not in comment


def test_supervisor_exception_is_in_comment(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """An exception from the supervisor verdict call reaches the comment."""
    env.prompt_llm.side_effect = [_reviewer(), RuntimeError("sup boom")]

    assert _run(tmp_path, config=REVIEW_PLAN) == 1

    assert "RuntimeError: sup boom" in _comment(env)


def test_fix_task_exception_is_in_comment_not_round_log(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A fix-task crash names the exception; the round log keeps the bare reason."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_TASKS), RuntimeError("fix boom")]

    assert _run(tmp_path, config=REVIEW_PLAN) == 1

    assert "RuntimeError: fix boom" in _comment(env)
    log = (tmp_path / "pr_info" / "plan_review_log_1.md").read_text(encoding="utf-8")
    assert "**Changes**:\ngeneral\n" in log
    assert "fix boom" not in log


def test_exception_traceback_is_logged_once(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``_fail`` logs the raised exception with its traceback exactly once."""
    error = RuntimeError("kaboom")
    env.prompt_llm.side_effect = error

    with caplog.at_level(logging.ERROR, logger=handoff.__name__):
        assert _run(tmp_path, config=REVIEW_PLAN) == 1

    records = [r for r in caplog.records if r.exc_info]
    assert len(records) == 1
    exc_info = records[0].exc_info
    assert exc_info is not None
    assert exc_info[1] is error
