"""Shared fixtures for vscodeclaude tests."""

from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.assessment import (
    IssueFacts,
    assess_issue_state,
)
from mcp_coder.workflows.vscodeclaude.types import (
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    Transition,
    VSCodeClaudeSession,
)

# Mock vscodeclaude config data for tests
MOCK_VSCODECLAUDE_CONFIGS: dict[str, dict[str, Any]] = {
    "status-01:created": {
        "emoji": "📝",
        "display_name": "ISSUE ANALYSIS",
        "stage_short": "new",
        "commands": ["/issue_analyse", "/discuss"],
        "color": "green",
    },
    "status-04:plan-review": {
        "emoji": "📋",
        "display_name": "PLAN REVIEW",
        "stage_short": "plan",
        "commands": ["/plan_review", "/discuss"],
        "color": "blue",
    },
    "status-07:code-review": {
        "emoji": "🔍",
        "display_name": "CODE REVIEW",
        "stage_short": "review",
        "commands": ["/implementation_review_supervisor"],
        "color": "yellow",
    },
    "status-10:pr-created": {
        "emoji": "🎉",
        "display_name": "PR CREATED",
        "stage_short": "pr",
    },
}


def _mock_get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Mock implementation for get_vscodeclaude_config."""
    return MOCK_VSCODECLAUDE_CONFIGS.get(status)


@pytest.fixture
def mock_vscodeclaude_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock get_vscodeclaude_config for workspace tests."""
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
        _mock_get_vscodeclaude_config,
    )


# ---------------------------------------------------------------------------
# Shared builders for the assessment test modules
# (test_assessment_layers / test_assessment_issue_facts /
# test_assessment_orchestration). Plain helpers, imported directly.
# ---------------------------------------------------------------------------


def make_signals(
    *,
    folder_exists: bool = True,
    title_match: bool = False,
    cmdline_match: bool = False,
    pid_alive: bool = False,
    found_pid: int | None = None,
    age_seconds: float = 0.0,
    within_grace: bool = False,
    directory_empty: bool = False,
) -> DetectionSignals:
    """Build DetectionSignals with everything off by default."""
    return DetectionSignals(
        folder_exists=folder_exists,
        title_match=title_match,
        cmdline_match=cmdline_match,
        pid_alive=pid_alive,
        found_pid=found_pid,
        age_seconds=age_seconds,
        within_grace=within_grace,
        directory_empty=directory_empty,
    )


def make_issue_facts(
    *,
    is_closed: bool = False,
    is_stale: bool = False,
    is_blocked: bool = False,
    is_unassigned: bool = False,
    is_ineligible: bool = False,
    stale_target: str | None = None,
) -> IssueFacts:
    """Build IssueFacts with everything off (i.e. eligible) by default."""
    return IssueFacts(
        is_closed=is_closed,
        is_stale=is_stale,
        is_blocked=is_blocked,
        is_unassigned=is_unassigned,
        is_ineligible=is_ineligible,
        stale_target=stale_target,
    )


def make_active(rule: LivenessRule = LivenessRule.TITLE) -> LivenessVerdict:
    """A live verdict."""
    return LivenessVerdict(active=True, rule=rule)


def make_inactive(rule: LivenessRule = LivenessRule.NO_MATCH) -> LivenessVerdict:
    """An inactive verdict."""
    return LivenessVerdict(active=False, rule=rule)


def make_eligible_state() -> IssueState:
    """An eligible (open, not stale/blocked/unassigned) issue state."""
    return assess_issue_state(make_issue_facts())


def make_stale_state(stale_target: str | None = "status-05:bot-pickup") -> IssueState:
    """A stale issue state (destruction candidate)."""
    return assess_issue_state(
        make_issue_facts(is_stale=True, stale_target=stale_target)
    )


NO_FLIP = Transition(flipped_to_inactive=False)


def make_session() -> VSCodeClaudeSession:
    """A minimal session for serializer/orchestration tests."""
    return VSCodeClaudeSession(
        folder="C:/work/issue-42",
        repo="owner/repo",
        issue_number=42,
        status="status-07:code-review",
        vscode_pid=None,
        vscode_pid_create_time=None,
        started_at="2026-06-26T00:00:00",
        is_intervention=False,
        last_active=None,
        last_active_rule=None,
    )


def make_session_at(folder: str, issue_number: int = 42) -> VSCodeClaudeSession:
    """A minimal session at a specific folder/issue for orchestration tests."""
    session = make_session()
    session["folder"] = folder
    session["issue_number"] = issue_number
    return session
