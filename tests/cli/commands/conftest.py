"""Shared test fixtures for CLI commands tests."""

from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_labels_config() -> Dict[str, Any]:
    """Fixture providing standard mock labels configuration.

    This fixture reduces duplication across coordinator tests by providing
    a consistent mock label configuration structure.

    Returns:
        Dict with 'workflow_labels' and 'ignore_labels' keys matching
        the structure from config/labels.json
    """
    return {
        "workflow_labels": [
            {
                "name": "status-02:awaiting-planning",
                "category": "bot_pickup",
                "internal_id": "awaiting_planning",
            },
            {
                "name": "status-03:planning",
                "category": "bot_busy",
                "internal_id": "planning",
            },
            {
                "name": "status-05:plan-ready",
                "category": "bot_pickup",
                "internal_id": "plan_ready",
            },
            {
                "name": "status-06:implementing",
                "category": "bot_busy",
                "internal_id": "implementing",
            },
            {
                "name": "status-08:ready-pr",
                "category": "bot_pickup",
                "internal_id": "ready_pr",
            },
            {
                "name": "status-09:pr-creating",
                "category": "bot_busy",
                "internal_id": "pr_creating",
            },
        ],
        "ignore_labels": ["Overview"],
    }


@pytest.fixture(autouse=True)
def _mock_verify_config() -> Generator[MagicMock, None, None]:
    """Auto-mock verify_config to return a default OK result.

    Tests that need a specific config result can override by patching
    verify_config explicitly inside the test body.
    """
    default = {
        "entries": [{"label": "Config file", "status": "ok", "value": "ok"}],
        "has_error": False,
    }
    with patch(
        "mcp_coder.cli.commands.verify.verify_config", return_value=default
    ) as mock:
        yield mock
