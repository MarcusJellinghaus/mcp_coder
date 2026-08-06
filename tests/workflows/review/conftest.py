"""Shared fixtures/helpers for the review after-steps + gate tests.

The ``env`` fixture patches every external the core loop + after-steps touch
and exposes the mocks; it is injected via pytest conftest discovery. The
``_status``/``_resp``/``_reviewer`` response builders, the ``_run`` workflow
entrypoint and the ``_label_transition`` assertion helper are plain functions
imported directly by the sibling test modules
(``test_core_after_steps`` and ``test_core_gates``).

Call order per round mirrors Step 7:
    1. fresh reviewer (``session_id=None``)               -> prompt_llm call
    2. supervisor verdict (persistent session)            -> prompt_llm call
    3. (only on a ``tasks`` verdict) reviewer resume       -> prompt_llm call
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.checks.branch_status import CIStatus
from mcp_coder.workflows.review import core, gates, handoff, reviewer, steps
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION

# --- verdict payloads -------------------------------------------------------

_DISMISS = '```json\n{"decision": "dismiss"}\n```'
_TASKS = '```json\n{"decision": "tasks", "tasks": ["Fix the bug at foo.py:1"]}\n```'

_REPORT = "foo.py:1 — high — something is wrong"
_REPORT_MEDIUM = "foo.py:1 — medium — a moderate concern"


def _status(
    text: str | None = None,
    undeterminable: bool = False,
    ci_status: CIStatus = CIStatus.PASSED,
) -> SimpleNamespace:
    """Build a branch-status stand-in with the fields the review loop reads."""
    return SimpleNamespace(
        pr_feedback_text=text,
        pr_feedback_undeterminable=undeterminable,
        ci_status=ci_status,
    )


def _resp(text: str, session_id: str = "sup-1") -> dict[str, Any]:
    """Build a minimal LLMResponseDict-shaped mock response."""
    return {
        "text": text,
        "session_id": session_id,
        "version": "1.0",
        "timestamp": "2026-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


def _reviewer(text: str = _REPORT, session_id: str = "rev-1") -> dict[str, Any]:
    """Reviewer response (distinct session id from the supervisor)."""
    return _resp(text, session_id=session_id)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every external the core loop + after-steps touch; expose the mocks."""
    mocks = SimpleNamespace()

    mocks.prompt_llm = MagicMock(name="prompt_llm")
    monkeypatch.setattr(reviewer, "prompt_llm", mocks.prompt_llm)

    monkeypatch.setattr(reviewer, "prepare_llm_environment", MagicMock(return_value={}))

    mocks.run_formatters = MagicMock(return_value=True)
    monkeypatch.setattr(core, "run_formatters", mocks.run_formatters)
    mocks.commit_changes = MagicMock(return_value=True)
    monkeypatch.setattr(core, "commit_changes", mocks.commit_changes)
    mocks.push_changes = MagicMock(return_value=True)
    monkeypatch.setattr(core, "push_changes", mocks.push_changes)

    # By default every round registers a change (dirty working dir).
    mocks.get_latest_commit_sha = MagicMock(return_value="SHA0")
    monkeypatch.setattr(core, "get_latest_commit_sha", mocks.get_latest_commit_sha)
    mocks.is_working_directory_clean = MagicMock(return_value=False)
    monkeypatch.setattr(
        core, "is_working_directory_clean", mocks.is_working_directory_clean
    )

    monkeypatch.setattr(
        steps, "get_current_branch_name", MagicMock(return_value="1072-review")
    )
    mocks.issue_manager = MagicMock(name="IssueManager")
    monkeypatch.setattr(handoff, "IssueManager", mocks.issue_manager)

    # Terminal-path log flush (handoff._flush_round_log commit + push): mocked so
    # the flush never touches real git; tests assert the commit fired.
    mocks.commit_all_changes = MagicMock(
        return_value={"success": True, "commit_hash": "FLUSHSHA"}
    )
    monkeypatch.setattr(handoff, "commit_all_changes", mocks.commit_all_changes)
    mocks.flush_push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "push_changes", mocks.flush_push)

    mocks.update_workflow_label = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "update_workflow_label", mocks.update_workflow_label)
    mocks.handle_workflow_failure = MagicMock()
    monkeypatch.setattr(
        handoff, "handle_workflow_failure", mocks.handle_workflow_failure
    )

    # After-steps externals: default to a clean rebase + green CI + a base branch.
    mocks.detect_base_branch = MagicMock(return_value="main")
    monkeypatch.setattr(steps, "detect_base_branch", mocks.detect_base_branch)
    mocks.attempt_rebase_and_push = MagicMock(return_value=True)
    monkeypatch.setattr(
        steps, "_attempt_rebase_and_push", mocks.attempt_rebase_and_push
    )
    mocks.check_and_fix_ci = MagicMock(return_value=True)
    monkeypatch.setattr(steps, "check_and_fix_ci", mocks.check_and_fix_ci)

    # PR-feedback fetch (implementation lane): default to a report with no open
    # feedback so existing tests see no note; individual tests override the
    # return value to exercise the threading.
    mocks.collect_branch_status = MagicMock(return_value=_status())
    monkeypatch.setattr(core, "collect_branch_status", mocks.collect_branch_status)

    # Gate 2 (exit guard) fetches branch status via gates.collect_branch_status,
    # a *separate* reference from the PR-feedback fetch above. Default to a
    # proven-green report so the dismiss path succeeds; individual tests override
    # the ci_status to exercise the guard.
    mocks.gate_collect_branch_status = MagicMock(return_value=_status())
    monkeypatch.setattr(
        gates, "collect_branch_status", mocks.gate_collect_branch_status
    )

    return mocks


def _run(project_dir: Path, **kwargs: Any) -> int:
    """Invoke the workflow (implementation lane) with label updates on."""
    params: dict[str, Any] = {
        "config": REVIEW_IMPLEMENTATION,
        "project_dir": project_dir,
        "provider": "claude",
        "update_issue_labels": True,
        "post_issue_comments": True,
    }
    params.update(kwargs)
    return core.run_review_workflow(**params)


def _label_transition(mock: MagicMock) -> tuple[str, str]:
    """Return the (from_label_id, to_label_id) of the last label update."""
    kwargs = mock.call_args.kwargs
    return kwargs["from_label_id"], kwargs["to_label_id"]
