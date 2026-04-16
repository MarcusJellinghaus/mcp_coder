"""Tests for verify_mcp_servers() health check (Steps 7–8)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.verification import verify_mcp_servers


def _make_tools_response(count: int) -> MagicMock:
    """Create a mock ListToolsResult with *count* tools."""
    tool_mocks = [MagicMock() for _ in range(count)]
    for mock in tool_mocks:
        mock.description = None
    result = MagicMock()
    result.tools = tool_mocks
    return result


def _make_tools_response_with_names(names: list[str]) -> MagicMock:
    """Create a mock ListToolsResult with named tools."""
    tool_mocks = [MagicMock() for _ in names]
    for mock, tool_name in zip(tool_mocks, names):
        mock.name = tool_name
        mock.description = None
    result = MagicMock()
    result.tools = tool_mocks
    return result


def _make_tools_response_with_descriptions(
    tools: list[tuple[str, str]],
) -> MagicMock:
    """Create a mock ListToolsResult with named tools and descriptions."""
    tool_mocks = [MagicMock() for _ in tools]
    for mock, (tool_name, desc) in zip(tool_mocks, tools):
        mock.name = tool_name
        mock.description = desc if desc else None
    result = MagicMock()
    result.tools = tool_mocks
    return result


class TestVerifyMcpServers:
    """Tests for verify_mcp_servers() function."""

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
        return_value={},
    )
    def test_no_config_returns_ok(self, _mock_load: MagicMock) -> None:
        """No servers configured → overall_ok True."""
        result = verify_mcp_servers("/fake/path/.mcp.json")
        assert result["overall_ok"] is True
        assert result["servers"] == {}
        assert result["value"] == "no servers configured"

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_server_success(self, mock_load: MagicMock) -> None:
        """Server responds with tools → ok True, tool count reported."""
        mock_load.return_value = {
            "tools-py": {
                "command": sys.executable,
                "args": ["-m", "tools"],
                "transport": "stdio",
            },
        }

        mock_session = AsyncMock()
        mock_session.list_tools.return_value = _make_tools_response(5)

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is True
        assert result["servers"]["tools-py"]["ok"] is True
        assert result["servers"]["tools-py"]["tools"] == 5
        assert "5 tools available" in result["servers"]["tools-py"]["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_server_failure(self, mock_load: MagicMock) -> None:
        """Server fails to start → ok False, error message."""
        mock_load.return_value = {
            "broken": {"command": "nonexistent", "args": [], "transport": "stdio"},
        }

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            side_effect=FileNotFoundError("executable not found")
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        assert result["servers"]["broken"]["ok"] is False
        assert result["servers"]["broken"]["error"] == "FileNotFoundError"
        assert "binary not found at nonexistent" in result["servers"]["broken"]["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_mixed_servers(self, mock_load: MagicMock) -> None:
        """One ok, one broken → overall_ok False, per-server details correct."""
        mock_load.return_value = {
            "good": {"command": sys.executable, "args": [], "transport": "stdio"},
            "bad": {"command": "nonexistent", "args": [], "transport": "stdio"},
        }

        good_session = AsyncMock()
        good_session.list_tools.return_value = _make_tools_response(3)

        def _session_side_effect(name: str) -> MagicMock:
            ctx = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=good_session)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        mock_client = MagicMock()
        mock_client.session.side_effect = _session_side_effect

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        assert result["servers"]["good"]["ok"] is True
        assert result["servers"]["good"]["tools"] == 3
        assert result["servers"]["bad"]["ok"] is False
        assert result["servers"]["bad"]["error"] == "FileNotFoundError"
        assert "binary not found at nonexistent (server bad)" in (
            result["servers"]["bad"]["value"]
        )

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_timeout_handling(self, mock_load: MagicMock) -> None:
        """Slow server → timeout error reported."""
        mock_load.return_value = {
            "slow": {"command": sys.executable, "args": [], "transport": "stdio"},
        }

        mock_session = AsyncMock()
        mock_session.list_tools.side_effect = asyncio.TimeoutError()

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json", timeout=1)

        assert result["overall_ok"] is False
        assert result["servers"]["slow"]["ok"] is False
        assert result["servers"]["slow"]["error"] == "TimeoutError"
        # Timeout must not be mislabeled as "failed to launch" (issue #830)
        value = result["servers"]["slow"]["value"]
        assert "timed out" in value
        assert "failed to launch" not in value

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_server_success_includes_tool_names(self, mock_load: MagicMock) -> None:
        """Successful server result includes tool_names list."""
        mock_load.return_value = {
            "tools-py": {
                "command": sys.executable,
                "args": ["-m", "tools"],
                "transport": "stdio",
            },
        }

        tool_names = ["read_file", "save_file", "edit_file"]
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = _make_tools_response_with_names(
            tool_names
        )

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        server_result = result["servers"]["tools-py"]
        assert server_result["ok"] is True
        assert server_result["tool_names"] == [
            ("read_file", ""),
            ("save_file", ""),
            ("edit_file", ""),
        ]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_server_success_includes_tool_descriptions(
        self, mock_load: MagicMock
    ) -> None:
        """Successful server result includes tool descriptions in tuples."""
        mock_load.return_value = {
            "workspace": {
                "command": sys.executable,
                "args": ["-m", "workspace"],
                "transport": "stdio",
            },
        }

        tools_with_descs = [
            ("read_file", "Read file contents"),
            ("save_file", "Write content to a file"),
            ("edit_file", ""),
        ]
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = _make_tools_response_with_descriptions(
            tools_with_descs
        )

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        server_result = result["servers"]["workspace"]
        assert server_result["ok"] is True
        assert server_result["tool_names"] == [
            ("read_file", "Read file contents"),
            ("save_file", "Write content to a file"),
            ("edit_file", ""),
        ]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_server_failure_has_no_tool_names(self, mock_load: MagicMock) -> None:
        """Failed server result does not contain tool_names."""
        # Use sys.executable so pre-flight (shutil.which) passes and the
        # mocked async context manager is actually reached.
        mock_load.return_value = {
            "broken": {"command": sys.executable, "args": [], "transport": "stdio"},
        }

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            side_effect=FileNotFoundError("executable not found")
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        server_result = result["servers"]["broken"]
        assert server_result["ok"] is False
        assert "tool_names" not in server_result

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_unresolved_placeholder_in_command(self, mock_load: MagicMock) -> None:
        """Unresolved ${VAR} in command → UnresolvedPlaceholder category."""
        mock_load.return_value = {
            "srv": {
                "command": "${MCP_CODER_VENV_PATH}\\foo.exe",
                "args": [],
                "transport": "stdio",
            },
        }

        result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        entry = result["servers"]["srv"]
        assert entry["ok"] is False
        assert entry["error"] == "UnresolvedPlaceholder"
        assert "${MCP_CODER_VENV_PATH}" in entry["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_unresolved_placeholder_in_args(self, mock_load: MagicMock) -> None:
        """Unresolved ${VAR} in args → UnresolvedPlaceholder category."""
        mock_load.return_value = {
            "srv": {
                "command": sys.executable,
                "args": ["--path", "${FOO_UNSET}"],
                "transport": "stdio",
            },
        }

        result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        entry = result["servers"]["srv"]
        assert entry["ok"] is False
        assert entry["error"] == "UnresolvedPlaceholder"
        assert "${FOO_UNSET}" in entry["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_unresolved_placeholder_in_env(self, mock_load: MagicMock) -> None:
        """Unresolved ${VAR} in env → UnresolvedPlaceholder category."""
        mock_load.return_value = {
            "srv": {
                "command": sys.executable,
                "args": [],
                "env": {"X": "${BAR_UNSET}"},
                "transport": "stdio",
            },
        }

        result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        entry = result["servers"]["srv"]
        assert entry["ok"] is False
        assert entry["error"] == "UnresolvedPlaceholder"
        assert "${BAR_UNSET}" in entry["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_launch_error_includes_resolved_path_and_class(
        self, mock_load: MagicMock
    ) -> None:
        """Launch error fallback includes resolved path and exception class."""
        mock_load.return_value = {
            "srv": {"command": sys.executable, "args": [], "transport": "stdio"},
        }

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            side_effect=ConnectionError("boom")
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        entry = result["servers"]["srv"]
        assert entry["ok"] is False
        assert entry["error"] == "ConnectionError"
        assert sys.executable in entry["value"]
        assert "ConnectionError" in entry["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_launch_error_filenotfound_after_preflight_passes(
        self, mock_load: MagicMock
    ) -> None:
        """Pre-flight passes but async session still raises FileNotFoundError."""
        mock_load.return_value = {
            "srv": {"command": sys.executable, "args": [], "transport": "stdio"},
        }

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            side_effect=FileNotFoundError("gone after preflight")
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification._import_mcp_client",
            return_value=lambda cfg: mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        entry = result["servers"]["srv"]
        assert entry["ok"] is False
        assert entry["error"] == "FileNotFoundError"
        assert sys.executable in entry["value"]
        assert "FileNotFoundError" in entry["value"]


@pytest.mark.langchain_integration
class TestMcpServerIntegration:
    """Integration tests for verify_mcp_servers() with real MCP config."""

    @staticmethod
    def _find_mcp_config() -> Path:
        """Locate .mcp.json in the project root, or skip."""
        # Walk up from this test file to find the project root
        candidate = Path(__file__).resolve().parents[4] / ".mcp.json"
        if candidate.is_file():
            return candidate
        # Fallback: check cwd
        cwd_candidate = Path.cwd() / ".mcp.json"
        if cwd_candidate.is_file():
            return cwd_candidate
        pytest.skip("No .mcp.json found")

    def test_verify_mcp_servers_with_real_config(self) -> None:
        """verify_mcp_servers() with a real .mcp.json reports per-server results."""
        config_path = self._find_mcp_config()

        result = verify_mcp_servers(str(config_path))

        assert "servers" in result
        assert isinstance(result["overall_ok"], bool)

        for name, server_result in result["servers"].items():
            assert "ok" in server_result, f"Server {name!r} missing 'ok' key"
            assert "value" in server_result, f"Server {name!r} missing 'value' key"
