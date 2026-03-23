"""Tests for verify_mcp_servers() health check (Step 7)."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.verification import verify_mcp_servers


def _make_tools_response(count: int) -> MagicMock:
    """Create a mock ListToolsResult with *count* tools."""
    tool_mocks = [MagicMock() for _ in range(count)]
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
                "command": "python",
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
            "mcp_coder.llm.providers.langchain.verification.MultiServerMCPClient",
            return_value=mock_client,
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
            "mcp_coder.llm.providers.langchain.verification.MultiServerMCPClient",
            return_value=mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        assert result["servers"]["broken"]["ok"] is False
        assert result["servers"]["broken"]["error"] == "FileNotFoundError"
        assert "executable not found" in result["servers"]["broken"]["value"]

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_mixed_servers(self, mock_load: MagicMock) -> None:
        """One ok, one broken → overall_ok False, per-server details correct."""
        mock_load.return_value = {
            "good": {"command": "python", "args": [], "transport": "stdio"},
            "bad": {"command": "nonexistent", "args": [], "transport": "stdio"},
        }

        good_session = AsyncMock()
        good_session.list_tools.return_value = _make_tools_response(3)

        def _session_side_effect(name: str) -> MagicMock:
            ctx = MagicMock()
            if name == "good":
                ctx.__aenter__ = AsyncMock(return_value=good_session)
                ctx.__aexit__ = AsyncMock(return_value=False)
            else:
                ctx.__aenter__ = AsyncMock(side_effect=ConnectionError("refused"))
                ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        mock_client = MagicMock()
        mock_client.session.side_effect = _session_side_effect

        with patch(
            "mcp_coder.llm.providers.langchain.verification.MultiServerMCPClient",
            return_value=mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json")

        assert result["overall_ok"] is False
        assert result["servers"]["good"]["ok"] is True
        assert result["servers"]["good"]["tools"] == 3
        assert result["servers"]["bad"]["ok"] is False
        assert result["servers"]["bad"]["error"] == "ConnectionError"

    @patch(
        "mcp_coder.llm.providers.langchain.verification._load_mcp_server_config",
    )
    def test_timeout_handling(self, mock_load: MagicMock) -> None:
        """Slow server → timeout error reported."""
        mock_load.return_value = {
            "slow": {"command": "python", "args": [], "transport": "stdio"},
        }

        mock_session = AsyncMock()
        mock_session.list_tools.side_effect = asyncio.TimeoutError()

        mock_client = MagicMock()
        mock_client.session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "mcp_coder.llm.providers.langchain.verification.MultiServerMCPClient",
            return_value=mock_client,
        ):
            result = verify_mcp_servers("/fake/path/.mcp.json", timeout=1)

        assert result["overall_ok"] is False
        assert result["servers"]["slow"]["ok"] is False
        assert result["servers"]["slow"]["error"] == "TimeoutError"
