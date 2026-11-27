"""The implementation lane commits the formatted tree before the CI gate on dismiss.

On a dismiss verdict the implementation lane runs a whole-tree, push-free
``_flush_round_log(FORMAT_BEFORE_GATE_MESSAGE)`` before ``_after_steps``: the
rebase push carries that commit, so the commit the CI gate judges is
formatted. The plan lane (``run_after_steps=False``) skips it.
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import commit
from mcp_coder.workflow_steps.commit import FormatterConfigError
from mcp_coder.workflows.review import handoff
from mcp_coder.workflows.review.config import REVIEW_PLAN
from mcp_coder.workflows.review.handoff import FORMAT_BEFORE_GATE_MESSAGE
from tests.workflows.review.conftest import _DISMISS, _resp, _reviewer, _run


def _commit_result(**overrides: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "success": True,
        "commit_hash": "FLUSHSHA",
        "error": None,
        "error_category": None,
        "returncode": 0,
        "stderr": "",
    }
    result.update(overrides)
    return result


def _messages(mock: MagicMock) -> list[str]:
    return [c.args[0] for c in mock.call_args_list]


def _review_records(caplog: pytest.LogCaptureFixture, level: int) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelno >= level and r.name.startswith("mcp_coder.workflows.review")
    ]


def test_pre_gate_commit_is_formatted_and_precedes_the_rebase(
    env: SimpleNamespace, tmp_path: Path, formatter_mocks: SimpleNamespace
) -> None:
    """Format, then commit with the pre-gate message, then rebase; no push first."""
    order: list[str] = []
    formatter_mocks.format_best_effort.side_effect = lambda *_a: order.append("format")

    def _commit(message: str, *_a: Any) -> dict[str, Any]:
        order.append(f"commit:{message}")
        return _commit_result()

    def _rebase(*_a: Any, **_k: Any) -> Any:
        order.append("rebase")
        return env.attempt_rebase_and_push.return_value

    def _push(*_a: Any) -> bool:
        order.append("flush_push")
        return True

    env.commit_all_changes.side_effect = _commit
    env.attempt_rebase_and_push.side_effect = _rebase
    env.flush_push.side_effect = _push
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    assert _run(tmp_path) == 0

    assert _messages(env.commit_all_changes)[0] == FORMAT_BEFORE_GATE_MESSAGE
    pre_gate = order.index(f"commit:{FORMAT_BEFORE_GATE_MESSAGE}")
    rebase = order.index("rebase")
    assert order[:pre_gate].count("format") == 1
    assert order[pre_gate - 1] == "format"
    assert pre_gate < rebase
    assert "flush_push" not in order[:rebase]
    env.commit_changes.assert_not_called()


def test_clean_tree_commits_nothing_and_stays_silent(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``commit_hash=None`` is a quiet no-op: no WARNING or ERROR record."""
    env.commit_all_changes.return_value = _commit_result(commit_hash=None)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    with caplog.at_level(logging.DEBUG):
        assert _run(tmp_path) == 0

    assert _messages(env.commit_all_changes)[0] == FORMAT_BEFORE_GATE_MESSAGE
    assert not _review_records(caplog, logging.WARNING)


def test_failed_pre_gate_commit_warns_and_the_review_continues(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed pre-gate commit logs a WARNING; ``_after_steps`` still runs."""
    env.commit_all_changes.side_effect = [
        _commit_result(success=False, commit_hash=None, error="boom"),
        _commit_result(),
    ]
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    with caplog.at_level(logging.WARNING):
        assert _run(tmp_path) == 0

    assert any(
        "Round-log commit did not succeed" in m
        for m in _review_records(caplog, logging.WARNING)
    )
    env.attempt_rebase_and_push.assert_called_once()


def test_failed_formatter_warns_and_still_commits(
    env: SimpleNamespace,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A raising formatter logs a WARNING; the pre-gate commit still happens."""
    monkeypatch.setattr(handoff, "format_best_effort", commit.format_best_effort)
    monkeypatch.setattr(
        commit,
        "run_formatters",
        MagicMock(side_effect=FormatterConfigError("bad toolkit")),
    )
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    with caplog.at_level(logging.WARNING):
        assert _run(tmp_path) == 0

    assert any(
        "Formatting failed before" in r.getMessage()
        for r in caplog.records
        if r.levelno == logging.WARNING
    )
    assert _messages(env.commit_all_changes)[0] == FORMAT_BEFORE_GATE_MESSAGE
    env.attempt_rebase_and_push.assert_called_once()


def test_plan_lane_skips_the_pre_gate_commit(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """``run_after_steps=False``: no commit with the pre-gate message."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    assert _run(tmp_path, config=REVIEW_PLAN) == 0

    assert FORMAT_BEFORE_GATE_MESSAGE not in _messages(env.commit_all_changes)
