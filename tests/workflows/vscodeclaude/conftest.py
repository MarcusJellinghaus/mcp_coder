"""Shared fixtures for vscodeclaude tests."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.assessment import (
    IssueFacts,
    assess_issue_state,
    assess_session,
)
from mcp_coder.workflows.vscodeclaude.types import (
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAssessment,
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


# ---------------------------------------------------------------------------
# Shared helpers for the status-display test modules.
# `_build_assessment` is a plain helper imported directly; `mock_status_checks`
# is a fixture auto-discovered via conftest collection.
# ---------------------------------------------------------------------------


def _build_assessment(
    session: VSCodeClaudeSession,
    *,
    is_closed: bool = False,
    is_running: bool = False,
    is_dirty: bool = False,
    is_stale: bool = False,
    is_ineligible: bool = False,
    stale_target: str | None = None,
) -> SessionAssessment:
    """Build the :class:`SessionAssessment` a status row renders.

    The status table now reads the assessment instead of recomputing liveness /
    staleness / git status, so tests inject one built from the same pure layer
    functions production uses (``assess_session``). Folder existence is detected
    from disk so missing-folder cases need no extra flag.
    """
    folder_exists = Path(session["folder"]).exists()
    if not folder_exists:
        git_status = "Missing"
    elif is_dirty:
        git_status = "Dirty"
    else:
        git_status = "Clean"
    signals = DetectionSignals(
        folder_exists=folder_exists,
        title_match=is_running,
        cmdline_match=False,
        pid_alive=False,
        found_pid=None,
        age_seconds=0.0,
        within_grace=False,
        directory_empty=not folder_exists,
    )
    issue_facts = IssueFacts(
        is_closed=is_closed,
        is_stale=is_stale,
        is_blocked=False,
        is_unassigned=False,
        is_ineligible=is_ineligible,
        stale_target=stale_target,
    )
    return assess_session(
        folder=session["folder"],
        signals=signals,
        issue_facts=issue_facts,
        git_status=git_status,
        directory_empty=not folder_exists,
        prior_last_active=None,
    )


@pytest.fixture
def mock_status_checks() -> Any:
    """Factory fixture returning a per-session assessment-map builder.

    The status table is now an assessment consumer: each session row renders its
    prebuilt :class:`SessionAssessment` rather than recomputing liveness /
    staleness / dirtiness. This fixture captures the desired state flags and
    returns a builder that, given the session, produces the ``assessments``
    argument for ``display_status_table``.

    Usage:
        def test_something(mock_status_checks):
            make_assessments = mock_status_checks(
                is_closed=False, is_running=False, is_dirty=False, is_stale=True
            )
            # ... pass assessments=make_assessments(session)
    """

    def _mock(
        is_closed: bool = False,
        is_running: bool = False,
        is_dirty: bool = False,
        is_stale: bool = True,
    ) -> Any:
        def _build(session: VSCodeClaudeSession) -> dict[str, SessionAssessment]:
            return {
                session["folder"]: _build_assessment(
                    session,
                    is_closed=is_closed,
                    is_running=is_running,
                    is_dirty=is_dirty,
                    is_stale=is_stale,
                )
            }

        return _build

    return _mock
