"""Shared test fixtures for CLI commands tests."""

from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import _LABEL_WIDTH, _MARKER_SLOT_WIDTH


def _expected_value_column(indent: int, *, label_width: int = _LABEL_WIDTH) -> int:
    """Return the 0-indexed column where the value SHOULD begin.

    Layout: [indent][label.ljust(label_width)][space][marker.ljust(_MARKER_SLOT_WIDTH)][space][value]
    Computed purely from layout constants; does NOT inspect any line.
    Use ``_assert_value_at_column`` to verify a real line against this.
    """
    return indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1


def _assert_value_at_column(line: str, expected_col: int) -> None:
    """Assert ``line`` has whitespace at ``expected_col - 1`` and a non-whitespace at ``expected_col``."""
    assert expected_col >= 1, f"expected_col must be >= 1; got {expected_col}"
    assert expected_col < len(
        line
    ), f"line shorter than expected value column {expected_col}: {line!r}"
    assert line[
        expected_col - 1
    ].isspace(), (
        f"prefix overflowed past col {expected_col - 1} (expected space): {line!r}"
    )
    assert not line[
        expected_col
    ].isspace(), f"value missing at col {expected_col} (expected non-space): {line!r}"


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


@pytest.fixture(autouse=True)
def _mock_verify_github() -> Generator[MagicMock, None, None]:
    """Auto-mock verify_github to return a default OK result.

    Tests that need a specific GitHub result can override by patching
    verify_github explicitly inside the test body.
    """
    default = {
        "token_configured": {"ok": True, "value": "configured"},
        "overall_ok": True,
    }
    with patch(
        "mcp_coder.cli.commands.verify.verify_github", return_value=default
    ) as mock:
        yield mock
