"""Tests for the /info slash command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.commands.help import register_help
from mcp_coder.icoder.core.commands.info import (
    _redact_env_vars,
    register_info,
)
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager, MCPServerStatus


@pytest.fixture
def runtime_info() -> RuntimeInfo:
    """Minimal RuntimeInfo for testing."""
    return RuntimeInfo(
        mcp_coder_version="0.1.0",
        python_version="3.11.0",
        claude_code_version="1.0.0",
        tool_env_path="C:\\tool_env",
        project_venv_path="C:\\project_venv",
        project_dir="C:\\project",
        env_vars={"MCP_CODER_PROJECT_DIR": "C:\\project"},
        mcp_servers=[],
    )


@pytest.fixture
def registry() -> CommandRegistry:
    """Fresh command registry."""
    return CommandRegistry()


# ── _redact_env_vars tests ──────────────────────────────────────────


def test_redact_env_vars_redacts_token() -> None:
    assert _redact_env_vars({"GITHUB_TOKEN": "abc"}) == {"GITHUB_TOKEN": "***"}


def test_redact_env_vars_redacts_key() -> None:
    assert _redact_env_vars({"API_KEY": "abc"}) == {"API_KEY": "***"}


def test_redact_env_vars_redacts_secret() -> None:
    assert _redact_env_vars({"MY_SECRET": "abc"}) == {"MY_SECRET": "***"}


def test_redact_env_vars_redacts_password() -> None:
    assert _redact_env_vars({"DB_PASSWORD": "x"}) == {"DB_PASSWORD": "***"}


def test_redact_env_vars_redacts_credential() -> None:
    assert _redact_env_vars({"CREDENTIAL_FILE": "x"}) == {"CREDENTIAL_FILE": "***"}


def test_redact_env_vars_case_insensitive() -> None:
    assert _redact_env_vars({"github_token": "abc"}) == {"github_token": "***"}


def test_redact_env_vars_preserves_safe() -> None:
    assert _redact_env_vars({"PATH": "/usr/bin"}) == {"PATH": "/usr/bin"}


def test_redact_env_vars_empty() -> None:
    assert _redact_env_vars({}) == {}


# ── /info command integration tests ────────────────────────────────


def test_info_command_registered(
    registry: CommandRegistry, runtime_info: RuntimeInfo
) -> None:
    register_info(registry, runtime_info)
    assert registry.has_command("/info")


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
@patch(
    "mcp_coder.icoder.core.commands.info.importlib.metadata.version",
    return_value="1.2.3",
)
def test_info_shows_version(
    _mock_version: object,
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "mcp-coder version: 1.2.3" in result.text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_python(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "Python:" in result.text
    import sys

    assert sys.executable in result.text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_environments(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "Tool env:" in result.text
    assert "Project env:" in result.text
    assert "Project dir:" in result.text
    assert "C:\\tool_env" in result.text
    assert "C:\\project_venv" in result.text
    assert "C:\\project" in result.text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_mcp_status(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    mock_manager = _make_mock_mcp_manager(
        [
            MCPServerStatus(name="tools-py", tool_count=12, connected=True),
            MCPServerStatus(name="workspace", tool_count=8, connected=False),
        ]
    )
    register_info(registry, runtime_info, mcp_manager=mock_manager)
    result = registry.dispatch("/info")
    assert result is not None
    assert "MCP servers (langchain):" in result.text
    assert "\u2713" in result.text  # ✓
    assert "\u2717" in result.text  # ✗
    assert "tools-py" in result.text
    assert "12 tools" in result.text
    assert "workspace" in result.text
    assert "8 tools" in result.text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_without_mcp_manager(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info, mcp_manager=None)
    result = registry.dispatch("/info")
    assert result is not None
    assert "MCP servers (langchain):" not in result.text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
@patch.dict(
    "os.environ",
    {"MCP_CODER_PROJECT_DIR": "/proj", "MCP_CODER_VENV_DIR": "/venv"},
    clear=False,
)
def test_info_shows_mcp_coder_env_vars(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "MCP_CODER_* env vars:" in result.text
    assert "MCP_CODER_PROJECT_DIR=" in result.text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
@patch.dict(
    "os.environ", {"GITHUB_TOKEN": "ghp_secret123", "SAFE_VAR": "hello"}, clear=False
)
def test_info_redacts_secrets_in_env(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "GITHUB_TOKEN=***" in result.text
    assert "ghp_secret123" not in result.text


def test_info_in_help(registry: CommandRegistry, runtime_info: RuntimeInfo) -> None:
    register_help(registry)
    register_info(registry, runtime_info)
    result = registry.dispatch("/help")
    assert result is not None
    assert "/info" in result.text


@patch("mcp_coder.icoder.core.commands.info.parse_claude_mcp_list", return_value=None)
@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_claude_mcp_list_unavailable(
    _mock_claude: object,
    _mock_parse: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "MCP servers (claude):" not in result.text


# ── helpers ─────────────────────────────────────────────────────────


class _FakeMCPManager:
    """Minimal stand-in for MCPManager in tests."""

    def __init__(self, statuses: list[MCPServerStatus]) -> None:
        self._statuses = statuses

    def status(self) -> list[MCPServerStatus]:
        return self._statuses


def _make_mock_mcp_manager(
    statuses: list[MCPServerStatus],
) -> MCPManager:
    """Create a fake MCPManager that returns given statuses."""
    return _FakeMCPManager(statuses)  # type: ignore[return-value]


# ── Prompt section in /info tests ───────────────────────────────────


@patch("mcp_coder.icoder.core.commands.info.load_prompts")
@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_prompt_paths(
    _mock_claude: object,
    mock_load: MagicMock,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    from mcp_coder.utils.pyproject_config import PromptsConfig

    mock_load.return_value = (
        "sys",
        "proj",
        PromptsConfig(
            system_prompt="prompts/system.md",
            project_prompt="prompts/project.md",
            claude_system_prompt_mode="replace",
        ),
    )
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "Prompts:" in result.text
    assert "prompts/system.md" in result.text
    assert "prompts/project.md" in result.text
    assert "replace" in result.text


@patch("mcp_coder.icoder.core.commands.info.load_prompts")
@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_shipped_defaults(
    _mock_claude: object,
    mock_load: MagicMock,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    from mcp_coder.utils.pyproject_config import PromptsConfig

    mock_load.return_value = (
        "sys",
        "proj",
        PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        ),
    )
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "(shipped default)" in result.text
    assert "append" in result.text
