"""Shared fixtures for vscodeclaude tests."""

from typing import Any

import pytest

# Mock vscodeclaude config data for tests
MOCK_VSCODECLAUDE_CONFIGS: dict[str, dict[str, Any]] = {
    "status-01:created": {
        "emoji": "📝",
        "display_name": "ISSUE ANALYSIS",
        "stage_short": "new",
        "commands": ["/issue_analyse", "/discuss"],
    },
    "status-04:plan-review": {
        "emoji": "📋",
        "display_name": "PLAN REVIEW",
        "stage_short": "plan",
        "commands": ["/plan_review", "/discuss"],
    },
    "status-07:code-review": {
        "emoji": "🔍",
        "display_name": "CODE REVIEW",
        "stage_short": "review",
        "commands": ["/implementation_review_supervisor"],
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
