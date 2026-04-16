"""Tests for agent utility functions (dependency checks, config, schema)."""

import builtins
import json
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Callable
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain.agent import (
    AGENT_MAX_STEPS,
    _check_agent_dependencies,
    _load_mcp_server_config,
    _resolve_env_vars,
    _sanitize_tool_schema,
)


class TestCheckAgentDependencies:
    """Tests for _check_agent_dependencies."""

    @staticmethod
    def _import_blocker(*blocked_packages: str) -> Callable[..., ModuleType]:
        """Return a side_effect for builtins.__import__ that blocks given packages."""
        _real_import = builtins.__import__

        def _fake_import(name: str, *args: Any, **kwargs: Any) -> ModuleType:
            for pkg in blocked_packages:
                if name == pkg or name.startswith(pkg + "."):
                    raise ImportError(f"No module named {name!r}")
            return _real_import(name, *args, **kwargs)

        return _fake_import

    def test_raises_when_both_missing(self) -> None:
        """Both packages missing -> ImportError listing both."""
        with patch(
            "builtins.__import__",
            side_effect=self._import_blocker("langchain_mcp_adapters", "langgraph"),
        ):
            with pytest.raises(ImportError, match="langchain-mcp-adapters") as exc_info:
                _check_agent_dependencies()
            assert "langgraph" in str(exc_info.value)

    def test_raises_when_one_missing(self) -> None:
        """Single package missing -> ImportError listing that package."""
        with patch(
            "builtins.__import__",
            side_effect=self._import_blocker("langgraph"),
        ):
            with pytest.raises(ImportError, match="langgraph"):
                _check_agent_dependencies()

    def test_passes_when_installed(self) -> None:
        """No error when packages are importable (conftest mocks provide them)."""
        # conftest auto-mocks both packages, so this should just pass
        _check_agent_dependencies()


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

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """Malformed JSON raises ValueError with user-friendly message."""
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Failed to parse MCP config file"):
            _load_mcp_server_config(str(cfg_file))

    def test_warns_on_non_stdio_transport(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-stdio transport logs a warning and falls back to stdio."""
        path = self._write_config(
            tmp_path,
            {"mcpServers": {"s": {"command": "cmd", "transport": "sse"}}},
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)
        assert "only 'stdio' is supported" in caplog.text
        assert "sse" in caplog.text
        assert result["s"]["transport"] == "stdio"

    def test_accepts_type_field(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Config with 'type': 'stdio' should not warn; output has transport=stdio."""
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "s": {
                        "command": "cmd",
                        "type": "stdio",
                    }
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)
        # No warning for "type" field
        assert "type" not in caplog.text
        # Output should have transport=stdio (forced)
        assert result["s"]["transport"] == "stdio"
        # 'type' must NOT appear in output — MultiServerMCPClient rejects it
        assert "type" not in result["s"]

    def test_type_field_excluded_from_output(self, tmp_path: Path) -> None:
        """'type' field from .mcp.json must not leak into server config dict.

        Regression test: MultiServerMCPClient passes all config keys to
        _create_stdio_session(), which raises TypeError on unknown kwargs.
        """
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "server-a": {
                        "type": "stdio",
                        "command": "echo",
                        "args": ["hello"],
                        "env": {"FOO": "bar"},
                    },
                    "server-b": {
                        "type": "stdio",
                        "command": "cat",
                    },
                }
            },
        )
        result = _load_mcp_server_config(path)
        for name in ("server-a", "server-b"):
            assert "type" not in result[name], f"'type' leaked into config for {name}"
            assert result[name]["transport"] == "stdio"


class TestSanitizeToolSchema:
    """Tests for _sanitize_tool_schema."""

    def test_adds_type_to_untyped_property(self) -> None:
        """Property with only 'title' gets 'type': 'string' added."""
        schema: dict[str, Any] = {
            "properties": {"content": {"title": "Content"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result["properties"]["content"]["type"] == "string"

    def test_preserves_existing_type(self) -> None:
        """Property with an existing 'type' is not modified."""
        schema: dict[str, Any] = {
            "properties": {"name": {"title": "Name", "type": "string"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result["properties"]["name"]["type"] == "string"

    def test_preserves_anyof(self) -> None:
        """Property using 'anyOf' is not modified."""
        schema: dict[str, Any] = {
            "properties": {
                "opts": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                }
            },
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert "type" not in result["properties"]["opts"]
        assert "anyOf" in result["properties"]["opts"]

    def test_preserves_ref(self) -> None:
        """Property using '$ref' is not modified."""
        schema: dict[str, Any] = {
            "properties": {"item": {"$ref": "#/definitions/Item"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert "type" not in result["properties"]["item"]

    def test_no_properties_returns_unchanged(self) -> None:
        """Schema without 'properties' is returned unchanged."""
        schema: dict[str, Any] = {"type": "object"}
        result = _sanitize_tool_schema(schema)
        assert result == {"type": "object"}

    def test_multiple_untyped_properties(self) -> None:
        """All untyped properties get default type."""
        schema: dict[str, Any] = {
            "properties": {
                "content": {"title": "Content"},
                "data": {"title": "Data"},
                "name": {"title": "Name", "type": "string"},
            },
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result["properties"]["content"]["type"] == "string"
        assert result["properties"]["data"]["type"] == "string"
        assert result["properties"]["name"]["type"] == "string"

    def test_does_not_mutate_original(self) -> None:
        """Original schema is not modified; a new copy is returned."""
        schema: dict[str, Any] = {
            "properties": {"x": {"title": "X"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result is not schema
        assert result["properties"]["x"]["type"] == "string"
        # Original must be untouched
        assert "type" not in schema["properties"]["x"]


class TestAgentConstants:
    """Verify module-level constants."""

    def test_max_steps_value(self) -> None:
        assert AGENT_MAX_STEPS == 50
