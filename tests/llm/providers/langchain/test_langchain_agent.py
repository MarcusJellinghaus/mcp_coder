"""Tests for agent utility functions (_resolve_env_vars, _load_mcp_server_config)."""

import json
import logging
from pathlib import Path

import pytest

from mcp_coder.llm.providers.langchain.agent import (
    AGENT_MAX_STEPS,
    _load_mcp_server_config,
    _resolve_env_vars,
)


class TestResolveEnvVars:
    """Tests for _resolve_env_vars."""

    def test_replaces_single_var(self) -> None:
        result = _resolve_env_vars("${HOME}/bin", {"HOME": "/usr/local"})
        assert result == "/usr/local/bin"

    def test_replaces_multiple_vars(self) -> None:
        result = _resolve_env_vars(
            "${USER}@${HOST}", {"USER": "alice", "HOST": "server1"}
        )
        assert result == "alice@server1"

    def test_preserves_unknown_vars(self) -> None:
        result = _resolve_env_vars("${KNOWN}/${UNKNOWN}", {"KNOWN": "ok"})
        assert result == "ok/${UNKNOWN}"

    def test_empty_string_unchanged(self) -> None:
        assert _resolve_env_vars("", {"A": "B"}) == ""

    def test_no_placeholders_unchanged(self) -> None:
        assert _resolve_env_vars("plain text", {"A": "B"}) == "plain text"


class TestLoadMcpServerConfig:
    """Tests for _load_mcp_server_config."""

    @staticmethod
    def _write_config(tmp_path: Path, config: dict[str, object]) -> str:
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps(config), encoding="utf-8")
        return str(cfg_file)

    def test_loads_and_resolves_config(self, tmp_path: Path) -> None:
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "myserver": {
                        "command": "${BIN}/server",
                        "args": ["--dir", "${PROJECT}"],
                        "env": {"PYTHONPATH": "${LIB}"},
                    }
                }
            },
        )
        result = _load_mcp_server_config(
            path, env_vars={"BIN": "/opt/bin", "PROJECT": "/code", "LIB": "/lib"}
        )
        assert result == {
            "myserver": {
                "command": "/opt/bin/server",
                "args": ["--dir", "/code"],
                "env": {"PYTHONPATH": "/lib"},
                "transport": "stdio",
            }
        }

    def test_env_vars_override_os_environ(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MY_VAR", "from_os")
        path = self._write_config(
            tmp_path,
            {"mcpServers": {"s": {"command": "${MY_VAR}"}}},
        )
        # env_vars should win over os.environ
        result = _load_mcp_server_config(path, env_vars={"MY_VAR": "override"})
        assert result["s"]["command"] == "override"

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            _load_mcp_server_config("/nonexistent/path/.mcp.json")

    def test_sets_stdio_transport(self, tmp_path: Path) -> None:
        path = self._write_config(
            tmp_path,
            {"mcpServers": {"s": {"command": "cmd", "transport": "sse"}}},
        )
        result = _load_mcp_server_config(path)
        # Always overridden to stdio
        assert result["s"]["transport"] == "stdio"

    def test_warns_on_unknown_fields(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "s": {
                        "command": "cmd",
                        "unknownField": "value123",
                    }
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)
        assert "unknownField" in caplog.text
        # Unknown field should not appear in output
        assert "unknownField" not in result["s"]


class TestAgentConstants:
    """Verify module-level constants."""

    def test_max_steps_value(self) -> None:
        assert AGENT_MAX_STEPS == 50
