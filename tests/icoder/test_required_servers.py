"""Required MCP servers at icoder start-up and in /info."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.commands.info import register_info
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import OutputText
from mcp_coder.icoder.env_setup import RuntimeInfo, setup_icoder_environment
from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.mcp_verification import (
    ClaudeMCPStatus,
    _exe_name,
    get_bin_dir,
)
from mcp_coder.utils.subprocess_runner import CommandResult

_ENV_SETUP = "mcp_coder.icoder.env_setup"
_INFO = "mcp_coder.icoder.core.commands.info"

_COMMAND_CONFIG = """\
[tool.mcp-coder.toolkit]
toolkit = "command"

[tool.mcp-coder.toolkit.command]
check.quick = [{ argv = ["npm", "run", "lint"], name = "lint" }]
"""

_MCP_LIST_OUTPUT = """\
Checking MCP server health...

mcp-workspace: /venv/bin/mcp-workspace --project-dir . - ✓ Connected
"""


def _ok(stdout: str) -> CommandResult:
    return CommandResult(return_code=0, stdout=stdout, stderr="", timed_out=False)


@pytest.fixture(name="command_project")
def _command_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A ``command`` project whose .mcp.json holds only mcp-workspace.

    The tool env ships the mcp-workspace binary but no mcp-tools-py.
    """
    monkeypatch.setattr(
        "mcp_coder.utils.toolkit_runner._toolkit_class",
        lambda _name: CommandToolkit,
    )
    project = tmp_path / "project"
    project.mkdir()
    (project / "mcp-coder.toml").write_text(_COMMAND_CONFIG, encoding="utf-8")
    (project / ".mcp.json").write_text(
        '{"mcpServers": {"mcp-workspace": {"command": "mcp-workspace"}}}',
        encoding="utf-8",
    )

    tool_env = tmp_path / "tool_env"
    bin_dir = get_bin_dir(tool_env)
    bin_dir.mkdir(parents=True)
    (bin_dir / _exe_name("mcp-workspace")).touch()

    monkeypatch.setattr(
        f"{_ENV_SETUP}.prepare_llm_environment",
        lambda project_dir: {
            "MCP_CODER_VENV_PATH": str(bin_dir),
            "MCP_CODER_VENV_DIR": str(tool_env),
            "MCP_CODER_PROJECT_DIR": str(project_dir),
        },
    )
    monkeypatch.setattr(f"{_ENV_SETUP}._get_claude_code_version", lambda: "1.2.3")
    monkeypatch.setattr(
        f"{_ENV_SETUP}.find_claude_executable", lambda **_kw: "/usr/bin/claude"
    )
    return project


def test_command_project_needs_only_mcp_workspace(
    command_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No mcp-tools-py anywhere: start-up succeeds and the Claude rows pass."""
    commands: list[list[str]] = []

    def _execute(command: list[str], **_kw: Any) -> CommandResult:
        commands.append(command)
        if command[-1] == "--version":
            return _ok("mcp-workspace 1.0\n")
        return _ok(_MCP_LIST_OUTPUT)

    monkeypatch.setattr("mcp_coder.utils.mcp_verification.execute_command", _execute)
    mcp_config = str(command_project / ".mcp.json")

    info = setup_icoder_environment(
        command_project, provider="langchain", mcp_config=mcp_config
    )

    assert info.required_mcp_servers == ("mcp-workspace",)
    assert info.mcp_config == mcp_config
    assert [s.name for s in info.mcp_servers] == ["mcp-workspace"]
    assert info.mcp_connection_status == [
        ClaudeMCPStatus(name="mcp-workspace", status_text="Connected", ok=True)
    ]
    mcp_list = commands[-1]
    assert mcp_list[mcp_list.index("--mcp-config") + 1] == mcp_config


def test_setup_passes_required_servers_and_config(
    command_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """parse_claude_mcp_list receives the required list and the config path."""
    monkeypatch.setattr(
        f"{_ENV_SETUP}.required_mcp_servers", lambda _p: ["mcp-workspace", "x"]
    )
    monkeypatch.setattr(f"{_ENV_SETUP}.verify_mcp_servers", lambda _root: [])
    parse = MagicMock(return_value=None)
    monkeypatch.setattr(f"{_ENV_SETUP}.parse_claude_mcp_list", parse)

    info = setup_icoder_environment(
        command_project, provider="langchain", mcp_config="custom.json"
    )

    assert info.required_mcp_servers == ("mcp-workspace", "x")
    assert info.mcp_config == "custom.json"
    args, kwargs = parse.call_args
    assert args[1] == ("mcp-workspace", "x")
    assert kwargs["mcp_config_path"] == "custom.json"


def _runtime_info(**overrides: Any) -> RuntimeInfo:
    fields: dict[str, Any] = {
        "mcp_coder_version": "0.1.0",
        "mcp_coder_utils_version": "0.2.0",
        "python_version": "3.11.0",
        "claude_code_version": "1.0.0",
        "tool_env_path": "/tool_env",
        "project_venv_path": "/project_venv",
        "project_dir": "/project",
        "env_vars": {"MCP_CODER_PROJECT_DIR": "/project"},
        "mcp_servers": [],
    }
    return RuntimeInfo(**(fields | overrides))


def test_runtime_info_defaults() -> None:
    """Older callers building RuntimeInfo get an empty list and no config."""
    info = _runtime_info()

    assert info.required_mcp_servers == ()
    assert info.mcp_config is None


@patch(f"{_INFO}.load_prompts")
@patch(f"{_INFO}.find_claude_executable", return_value="/usr/bin/claude")
def test_info_passes_required_list_and_prints_not_listed(
    _mock_claude: object,
    mock_load: MagicMock,
    event_log: EventLog,
) -> None:
    """/info uses the stored list and config, and shows a "not listed" server."""
    from mcp_coder.utils.pyproject_config import PromptsConfig

    mock_load.return_value = (
        "",
        "",
        PromptsConfig(
            system_prompt=None, project_prompt=None, claude_system_prompt_mode="append"
        ),
    )
    runtime_info = _runtime_info(
        required_mcp_servers=("mcp-workspace", "x"), mcp_config="custom.json"
    )
    statuses = [
        ClaudeMCPStatus(name="mcp-workspace", status_text="Connected", ok=True),
        ClaudeMCPStatus(name="x", status_text="not listed", ok=False),
    ]
    registry = CommandRegistry()
    register_info(registry, runtime_info, event_log)

    with patch(f"{_INFO}.parse_claude_mcp_list", return_value=statuses) as parse:
        response = registry.dispatch("/info")

    args, kwargs = parse.call_args
    assert args[1] == ("mcp-workspace", "x")
    assert kwargs["mcp_config_path"] == "custom.json"
    assert response is not None
    text = "\n".join(a.text for a in response.actions if isinstance(a, OutputText))
    assert "  x: ✗ not listed" in text
    assert "  mcp-workspace: ✓ Connected" in text
