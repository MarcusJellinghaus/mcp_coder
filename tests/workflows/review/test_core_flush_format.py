"""Core-level checks that the review formats before its whole-tree flushes.

``_flush_round_log`` formats only when it commits the whole tree (the dismiss
flush and the ``_fail`` flushes). The scoped flushes (``only=``: the top of
the loop, ``_route_to_human``, the rounds cap) never format.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tests.workflows.review.conftest import _DISMISS, _TASKS, _resp, _reviewer, _run

_ESCALATE = '```json\n{"decision": "escalate", "escalate_reason": "needs a human"}\n```'


def test_dismiss_flush_formats_and_commits_the_tree(
    env: SimpleNamespace, tmp_path: Path, formatter_mocks: SimpleNamespace
) -> None:
    """A round-1 dismiss formats, then lands its log with a whole-tree commit."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    assert _run(tmp_path) == 0

    assert formatter_mocks.format_best_effort.call_count >= 1
    env.commit_all_changes.assert_called()


def test_escalate_flush_is_scoped_and_unformatted(
    env: SimpleNamespace, tmp_path: Path, formatter_mocks: SimpleNamespace
) -> None:
    """``_route_to_human`` commits only the log and never formats."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_ESCALATE)]

    assert _run(tmp_path) == 0

    env.commit_paths.assert_called()
    env.commit_all_changes.assert_not_called()
    formatter_mocks.format_best_effort.assert_not_called()


def test_commit_failed_flush_formats_before_the_commit(
    env: SimpleNamespace, tmp_path: Path, formatter_mocks: SimpleNamespace
) -> None:
    """The ``commit-failed`` path formats, then commits the whole tree."""
    order: list[str] = []
    formatter_mocks.format_best_effort.side_effect = lambda *_a: order.append("format")
    flush_result: dict[str, Any] = env.commit_all_changes.return_value

    def _commit(*_a: Any) -> dict[str, Any]:
        order.append("commit")
        return flush_result

    env.commit_all_changes.side_effect = _commit
    env.commit_changes.return_value = False
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
    ]

    assert _run(tmp_path) == 1

    assert order == ["format", "commit"]
    assert formatter_mocks.format_best_effort.call_args.args[0] == tmp_path
