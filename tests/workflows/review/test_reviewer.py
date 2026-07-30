"""Unit tests for reviewer turn helpers — the ``pr_note`` / ``ci_note`` seams.

These isolate :func:`_run_reviewer`'s prompt assembly by mocking ``prompt_llm``,
``prepare_llm_environment`` and ``get_prompt`` (so the fresh-review header is a
known template, independent of ``prompts.md``).
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.review import reviewer
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION


@pytest.fixture
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock the reviewer's LLM + env + prompt loading; return the prompt_llm mock."""
    m = MagicMock(name="prompt_llm", return_value={"text": "ok", "session_id": "rev-1"})
    monkeypatch.setattr(reviewer, "prompt_llm", m)
    monkeypatch.setattr(reviewer, "prepare_llm_environment", MagicMock(return_value={}))
    monkeypatch.setattr(
        reviewer,
        "get_prompt",
        MagicMock(return_value="HEADER {issue_number} {base_branch}"),
    )
    return m


def _call(**overrides: Any) -> None:
    """Invoke _run_reviewer with sensible defaults, applying overrides."""
    kwargs: dict[str, Any] = dict(
        config=REVIEW_IMPLEMENTATION,
        project_dir=Path("/p"),
        provider="claude",
        mcp_config=None,
        settings_file=None,
        execution_dir=None,
        issue_number=1,
        base_branch="main",
        session_id=None,
        tasks=None,
    )
    kwargs.update(overrides)
    reviewer._run_reviewer(**kwargs)


def test_fresh_review_appends_pr_note(mock_llm: MagicMock) -> None:
    """A fresh review appends pr_note to the tail of the prompt."""
    _call(pr_note="PR-NOTE")

    prompt = mock_llm.call_args.args[0]
    assert prompt.endswith("PR-NOTE")


def test_fresh_review_appends_both_ci_and_pr_notes(mock_llm: MagicMock) -> None:
    """ci_note and pr_note are both appended, pr_note last."""
    _call(ci_note="CI-NOTE", pr_note="PR-NOTE")

    prompt = mock_llm.call_args.args[0]
    assert "CI-NOTE" in prompt
    assert prompt.endswith("PR-NOTE")


def test_fresh_review_without_pr_note_appends_nothing(mock_llm: MagicMock) -> None:
    """No pr_note -> the note text is absent from the prompt."""
    _call()

    prompt = mock_llm.call_args.args[0]
    assert "PR-NOTE" not in prompt


def test_task_resume_ignores_pr_note(mock_llm: MagicMock) -> None:
    """A task-application resume ignores pr_note entirely."""
    _call(session_id="rev-1", tasks=["Fix foo.py:1"], pr_note="PR-NOTE")

    prompt = mock_llm.call_args.args[0]
    assert "PR-NOTE" not in prompt
    assert "Fix foo.py:1" in prompt
