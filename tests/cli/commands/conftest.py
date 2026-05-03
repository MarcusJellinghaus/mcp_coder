"""Shared test fixtures for CLI commands tests."""

from contextlib import contextmanager
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (
    _LABEL_WIDTH,
    _MARKER_SLOT_WIDTH,
    _format_row,
)
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus


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


@contextmanager
def _make_verify_mocks() -> Generator[Dict[str, MagicMock], None, None]:
    """Patch the additional execute_verify mock surface for alignment smoke tests.

    Composes with the autouse ``_mock_verify_config`` and ``_mock_verify_github``
    fixtures (does NOT re-patch them). Mocks ``_collect_mcp_warnings`` to ``[]``
    so the dynamic-width MCP CONFIG WARNINGS section is excluded from output;
    that per-section invariant is asserted in step_4.md tests. Exists in
    conftest so the alignment smoke test can drive ``execute_verify`` once.
    """
    _verify = "mcp_coder.cli.commands.verify"
    _lc_verify = "mcp_coder.llm.providers.langchain.verification"

    minimal_llm_response: Dict[str, Any] = {
        "version": "1.0",
        "timestamp": "2026-01-01T00:00:00",
        "text": "OK",
        "session_id": None,
        "provider": "claude",
        "raw_response": {},
    }
    claude_ok: Dict[str, Any] = {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }
    mlflow_not_installed: Dict[str, Any] = {
        "installed": {"ok": False, "value": "not installed"},
        "overall_ok": True,
    }
    mcp_servers_ok: Dict[str, Any] = {
        "servers": {
            "mcp-tools-py": {
                "ok": True,
                "value": "3 tools",
                "tool_names": [
                    ("read_file", "Read"),
                    ("save_file", "Save"),
                    ("edit_file", "Edit"),
                ],
            }
        },
        "overall_ok": True,
    }
    claude_mcp_statuses = [
        ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
    ]
    smoke_row = _format_row("MCP edit smoke test", "[OK]", "edit verified", indent=2)

    with (
        patch(
            f"{_verify}.resolve_llm_method", return_value=("claude", "default")
        ) as resolve_llm,
        patch(f"{_verify}.verify_claude", return_value=claude_ok) as verify_claude_mock,
        patch(
            f"{_verify}.verify_mlflow", return_value=mlflow_not_installed
        ) as verify_mlflow_mock,
        patch(
            f"{_lc_verify}.verify_mcp_servers", return_value=mcp_servers_ok
        ) as verify_mcp_servers_mock,
        patch(
            f"{_verify}.prepare_llm_environment", return_value={"K": "V"}
        ) as prepare_env_mock,
        patch(
            f"{_verify}.parse_claude_mcp_list", return_value=claude_mcp_statuses
        ) as parse_mcp_mock,
        patch(
            f"{_verify}.prompt_llm", return_value=minimal_llm_response
        ) as prompt_mock,
        patch(
            f"{_verify}._run_mcp_edit_smoke_test", return_value=smoke_row
        ) as smoke_mock,
        patch(
            f"{_verify}._collect_mcp_warnings", return_value=[]
        ) as collect_warnings_mock,
        patch(f"{_verify}.log_to_mlflow", create=True) as log_mlflow_mock,
        patch(
            f"{_verify}.resolve_mcp_config_path", return_value="/fake/.mcp.json"
        ) as resolve_mcp_mock,
        patch(
            f"{_verify}.find_claude_executable", return_value=None
        ) as find_claude_mock,
    ):
        yield {
            "resolve_llm_method": resolve_llm,
            "verify_claude": verify_claude_mock,
            "verify_mlflow": verify_mlflow_mock,
            "verify_mcp_servers": verify_mcp_servers_mock,
            "prepare_llm_environment": prepare_env_mock,
            "parse_claude_mcp_list": parse_mcp_mock,
            "prompt_llm": prompt_mock,
            "_run_mcp_edit_smoke_test": smoke_mock,
            "_collect_mcp_warnings": collect_warnings_mock,
            "log_to_mlflow": log_mlflow_mock,
            "resolve_mcp_config_path": resolve_mcp_mock,
            "find_claude_executable": find_claude_mock,
        }
