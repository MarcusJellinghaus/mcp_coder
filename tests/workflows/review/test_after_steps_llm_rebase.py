"""Review's rebase gate runs the LLM fallback; the hand-off names its reason.

``_after_steps`` is called directly against the shared ``env`` fixture in
``conftest``, whose ``attempt_rebase_and_push`` mock stands in for
``steps.rebase_with_llm_fallback``.
"""

import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.review import handoff, steps
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION

# --- _after_steps ----------------------------------------------------------


def _after_steps(tmp_path: Path) -> tuple[str | None, RebaseOutcome | None, str | None]:
    """Run the implementation-lane after-steps with a broad settings file."""
    return steps._after_steps(
        REVIEW_IMPLEMENTATION,
        tmp_path,
        "claude",
        "mcp.json",
        "broad-settings.json",
        is_dismiss=True,
    )


def test_rebase_gate_calls_helper_without_settings_override(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """The helper gets provider and mcp_config; the job's settings stay with CI."""
    _after_steps(tmp_path)

    env.attempt_rebase_and_push.assert_called_once_with(tmp_path, "claude", "mcp.json")
    assert env.check_and_fix_ci.call_args.kwargs["settings_file"] == (
        "broad-settings.json"
    )


def test_non_ok_outcome_returns_rebase_and_skips_ci(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """A non-ok helper outcome returns ``("rebase", outcome, None)``."""
    outcome = RebaseOutcome(
        "conflict", "main", "abc1234", llm_detail="binary conflict in x.png"
    )
    env.attempt_rebase_and_push.return_value = outcome

    assert _after_steps(tmp_path) == ("rebase", outcome, None)
    env.check_and_fix_ci.assert_not_called()


def test_ok_outcome_runs_ci_gate_on_pushed_sha(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """An ok helper outcome runs the CI gate pinned to the pushed SHA."""
    outcome = RebaseOutcome("ok", "main", "abc1234", llm_detail="resolved")
    env.attempt_rebase_and_push.return_value = outcome

    assert _after_steps(tmp_path) == (None, outcome, None)
    env.check_and_fix_ci.assert_called_once()
    assert env.check_and_fix_ci.call_args.kwargs["expected_sha"] == "PUSHEDSHA"


# --- _route_to_human: LLM rebase field --------------------------------------


@pytest.fixture
def routed(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the externals ``_route_to_human`` touches; return the IssueManager."""
    monkeypatch.setattr(handoff, "_flush_round_log", MagicMock())
    monkeypatch.setattr(handoff, "apply_final_label", MagicMock(return_value=0))
    issue_manager = MagicMock(name="IssueManager")
    monkeypatch.setattr(handoff, "IssueManager", issue_manager)
    return issue_manager


def _handoff_lines(
    issue_manager: MagicMock, tmp_path: Path, rebase: RebaseOutcome
) -> list[str]:
    """Route a rebase hand-off and return the posted comment's lines."""
    handoff._route_to_human(
        REVIEW_IMPLEMENTATION,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=True,
        log_path=None,
        round_number=1,
        start_time=time.time(),
        rebase=rebase,
    )
    body: str = issue_manager.return_value.add_comment.call_args.args[1]
    return body.splitlines()


def test_handoff_renders_llm_rebase_detail(routed: MagicMock, tmp_path: Path) -> None:
    """``llm_detail`` renders as the LLM rebase field; the table fields stay."""
    category, _, next_step = handoff._REBASE_HANDOFF["conflict"]
    rebase = RebaseOutcome(
        "conflict", "main", "abc1234", llm_detail="binary conflict in x.png"
    )

    lines = _handoff_lines(routed, tmp_path, rebase)

    assert "**LLM rebase:** binary conflict in x.png" in lines
    assert f"**Category:** {category}" in lines
    assert f"**Next step:** {next_step}" in lines


def test_handoff_without_llm_detail_has_no_llm_rebase_line(
    routed: MagicMock, tmp_path: Path
) -> None:
    """Without ``llm_detail`` no LLM rebase line appears."""
    lines = _handoff_lines(routed, tmp_path, RebaseOutcome("conflict", "main", "a1"))

    assert not any("LLM rebase" in line for line in lines)
