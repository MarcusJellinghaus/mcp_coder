"""Pure-function tests for the ``format_runtime_banner`` helper."""

from __future__ import annotations

from pathlib import Path

from mcp_coder.icoder.ui.runtime_banner import format_runtime_banner
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus, MCPServerInfo


def test_live_runtime_info_shape() -> None:
    """Live RuntimeInfo-shaped dict produces the expected line set."""
    data: dict[str, object] = {
        "mcp_coder_version": "1.2.3",
        "mcp_coder_utils_version": "4.5.6",
        "tool_env_path": "/tool",
        "project_venv_path": "/proj/.venv",
        "project_dir": "/proj",
        "mcp_servers": [
            MCPServerInfo(name="srv-a", path=Path("/srv-a"), version="9.0"),
        ],
        "mcp_connection_status": None,
    }
    lines = format_runtime_banner(data)
    assert lines == [
        "mcp-coder 1.2.3",
        "mcp-coder-utils 4.5.6",
        "srv-a 9.0",
        "Tool env:    /tool",
        "Project env: /proj/.venv",
        "Project dir: /proj",
    ]


def test_session_start_shape_no_status() -> None:
    """Session-start payload uses ``tool_env``/``project_venv`` and dict servers."""
    data: dict[str, object] = {
        "mcp_coder_version": "1.2.3",
        "tool_env": "/tool",
        "project_venv": "/proj/.venv",
        "project_dir": "/proj",
        "mcp_servers": {"srv-a": "9.0"},
    }
    lines = format_runtime_banner(data)
    assert lines == [
        "mcp-coder 1.2.3",
        "srv-a 9.0",
        "Tool env:    /tool",
        "Project env: /proj/.venv",
        "Project dir: /proj",
    ]


def test_missing_mcp_servers_key_is_safe() -> None:
    """Missing ``mcp_servers`` key produces no server lines and no exception."""
    lines = format_runtime_banner({"mcp_coder_version": "x"})
    assert lines == ["mcp-coder x"]


def test_missing_mcp_coder_version_defaults_to_unknown() -> None:
    """Missing version key falls back to ``unknown``."""
    lines = format_runtime_banner({})
    assert lines == ["mcp-coder unknown"]


def test_connection_status_live_shape_ok_and_error() -> None:
    """List of ClaudeMCPStatus produces correct ok/error suffixes."""
    data: dict[str, object] = {
        "mcp_coder_version": "1",
        "mcp_servers": [
            MCPServerInfo(name="ok-srv", path=Path("/ok"), version="1.0"),
            MCPServerInfo(name="bad-srv", path=Path("/bad"), version="2.0"),
        ],
        "mcp_connection_status": [
            ClaudeMCPStatus(name="ok-srv", status_text="Connected", ok=True),
            ClaudeMCPStatus(name="bad-srv", status_text="Failed to start", ok=False),
        ],
    }
    lines = format_runtime_banner(data)
    assert "ok-srv 1.0  ✓ Connected" in lines
    assert "bad-srv 2.0  ✗ Failed to start" in lines


def test_connection_status_dict_replay_shape() -> None:
    """Dict-of-name shape (session_start replay) produces the same suffixes."""
    data: dict[str, object] = {
        "mcp_coder_version": "1",
        "mcp_servers": {"ok-srv": "1.0", "bad-srv": "2.0"},
        "mcp_connection_status": {
            "ok-srv": {"ok": True, "status_text": "Connected"},
            "bad-srv": {"ok": False, "status_text": "Failed to start"},
        },
    }
    lines = format_runtime_banner(data)
    assert "ok-srv 1.0  ✓ Connected" in lines
    assert "bad-srv 2.0  ✗ Failed to start" in lines


def test_mcp_servers_list_of_dicts_shape() -> None:
    """List-of-dicts is also a valid input shape for ``mcp_servers``."""
    data: dict[str, object] = {
        "mcp_coder_version": "1",
        "mcp_servers": [{"name": "srv-a", "version": "9.0"}],
    }
    lines = format_runtime_banner(data)
    assert "srv-a 9.0" in lines


def test_status_present_but_server_missing_yields_no_suffix() -> None:
    """Status list without a matching entry leaves the line bare (no trailing space)."""
    data: dict[str, object] = {
        "mcp_coder_version": "1",
        "mcp_servers": [
            MCPServerInfo(name="srv-a", path=Path("/a"), version="9.0"),
        ],
        "mcp_connection_status": [
            ClaudeMCPStatus(name="other", status_text="Connected", ok=True),
        ],
    }
    lines = format_runtime_banner(data)
    assert "srv-a 9.0" in lines
