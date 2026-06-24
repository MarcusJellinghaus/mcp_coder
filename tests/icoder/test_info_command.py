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
from mcp_coder.icoder.core.types import OutputText, Response
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager, MCPServerStatus


def _info_text(response: Response | None) -> str:
    """Join the text of all OutputText actions in a response."""
    assert response is not None
    return "\n".join(a.text for a in response.actions if isinstance(a, OutputText))


@pytest.fixture
def runtime_info() -> RuntimeInfo:
    """Minimal RuntimeInfo for testing."""
    return RuntimeInfo(
        mcp_coder_version="0.1.0",
        mcp_coder_utils_version="0.2.0",
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
def test_info_shows_versions(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    text = _info_text(result)
    assert "mcp-coder version: 0.1.0" in text
    assert "mcp-coder-utils version: 0.2.0" in text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_python(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    text = _info_text(result)
    assert "Python:" in text
    import sys

    assert sys.executable in text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_environments(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    text = _info_text(result)
    assert "Tool env:" in text
    assert "Project env:" in text
    assert "Project dir:" in text
    assert "C:\\tool_env" in text
    assert "C:\\project_venv" in text
    assert "C:\\project" in text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_mcp_status(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    mock_manager = _make_mock_mcp_manager(
        [
            MCPServerStatus(name="mcp-tools-py", tool_count=12, connected=True),
            MCPServerStatus(name="mcp-workspace", tool_count=8, connected=False),
        ]
    )
    register_info(registry, runtime_info, mcp_manager=mock_manager)
    result = registry.dispatch("/info")
    text = _info_text(result)
    assert "MCP servers (langchain):" in text
    assert "\u2713" in text  # ✓
    assert "\u2717" in text  # ✗
    assert "mcp-tools-py" in text
    assert "12 tools" in text
    assert "mcp-workspace" in text
    assert "8 tools" in text


@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_without_mcp_manager(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info, mcp_manager=None)
    result = registry.dispatch("/info")
    assert "MCP servers (langchain):" not in _info_text(result)


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
    text = _info_text(result)
    assert "MCP_CODER_* env vars:" in text
    assert "MCP_CODER_PROJECT_DIR=" in text


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
    text = _info_text(result)
    assert "GITHUB_TOKEN=***" in text
    assert "ghp_secret123" not in text


def test_info_in_help(registry: CommandRegistry, runtime_info: RuntimeInfo) -> None:
    register_help(registry)
    register_info(registry, runtime_info)
    result = registry.dispatch("/help")
    assert "/info" in _info_text(result)


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
    assert "MCP servers (claude):" not in _info_text(result)


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
    text = _info_text(result)
    assert "Prompts:" in text
    assert "prompts/system.md" in text
    assert "prompts/project.md" in text
    assert "replace" in text


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
    text = _info_text(result)
    assert "(shipped default)" in text
    assert "append" in text
