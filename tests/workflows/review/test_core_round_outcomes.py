"""Review-loop tests for what a round records and passes on.

These drive :func:`run_review_workflow` with the shared ``env`` fixture from
``conftest`` (all LLM and git externals mocked). Call order per round:
fresh reviewer, supervisor verdict, then (on ``tasks``) the reviewer resume.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tests.workflows.review.conftest import _DISMISS, _resp, _run


def _final_resp(text: str, result: str, session_id: str = "rev-1") -> dict[str, Any]:
    """Reviewer response whose ``raw_response`` events end in a ``done`` event."""
    response = _resp(text, session_id=session_id)
    response["raw_response"] = {
        "events": [
            {"type": "text_delta", "text": text},
            {"type": "done", "result": result},
        ]
    }
    return response


def _log(tmp_path: Path) -> str:
    """Read the round log of the implementation lane's first run."""
    return (tmp_path / "pr_info" / "implementation_review_log_1.md").read_text(
        encoding="utf-8"
    )


def test_round_uses_the_final_reviewer_message(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Narration before the final message reaches neither the log nor the supervisor."""
    env.prompt_llm.side_effect = [
        _final_resp("Still reviewing.a.py:1 — high — x", "a.py:1 — high — x"),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    log = _log(tmp_path)
    assert "a.py:1 — high — x" in log
    assert "Still reviewing" not in log
    supervisor_prompt = env.prompt_llm.call_args_list[1].args[0]
    assert "Still reviewing" not in supervisor_prompt


def test_empty_final_message_falls_back_without_retry(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """An empty final result uses the joined text; the empty-report retry stays off."""
    env.prompt_llm.side_effect = [
        _final_resp("a.py:1 — high — x", ""),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    assert env.prompt_llm.call_count == 2
