"""``verify`` reports every required MCP server from ``claude mcp list``.

A required server missing from the output gets an ``[ERR] not listed`` row,
which fails ``verify`` for provider ``claude`` and is informational otherwise.
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.utils.mcp_verification import parse_claude_mcp_list
from mcp_coder.utils.subprocess_runner import CommandResult

from .conftest import _LC_VERIFY, _VERIFY, _langchain_ok, _make_args, _make_verify_mocks

_MCP_LIST_OUTPUT = """\
Checking MCP server health...

mcp-workspace: /venv/bin/mcp-workspace --project-dir . - ✓ Connected
"""


@pytest.fixture(name="claude_mcp_list")
def _claude_mcp_list() -> Generator[dict[str, MagicMock], None, None]:
    """execute_verify mocks with the real parser over a fixed ``claude mcp list``."""
    with (
        _make_verify_mocks() as mocks,
        patch(
            "mcp_coder.utils.mcp_verification.execute_command",
            return_value=CommandResult(
                return_code=0, stdout=_MCP_LIST_OUTPUT, stderr="", timed_out=False
            ),
        ) as execute,
    ):
        mocks["find_claude_executable"].return_value = "/usr/bin/claude"
        mocks["parse_claude_mcp_list"].side_effect = parse_claude_mcp_list
        mocks["execute_command"] = execute
        yield mocks


def _run(required: list[str]) -> int:
    with patch(f"{_VERIFY}.required_mcp_servers", return_value=required):
        return execute_verify(_make_args())


def _claude_rows(output: str) -> list[str]:
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if "via Claude Code" in line)
    return [line for line in lines[start + 1 :] if line.strip()][:3]


def test_all_required_listed_exit_0(
    claude_mcp_list: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
) -> None:
    """Control: every required server connected → exit 0."""
    assert _run(["mcp-workspace"]) == 0
    assert "not listed" not in capsys.readouterr().out


def test_not_listed_fails_for_claude(
    claude_mcp_list: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
) -> None:
    """A required server absent from ``claude mcp list`` → [ERR] row, exit 1."""
    exit_code = _run(["mcp-workspace", "x"])
    output = capsys.readouterr().out

    assert exit_code == 1
    row = next(line for line in _claude_rows(output) if line.strip().startswith("x"))
    assert "[ERR]" in row
    assert "not listed" in row


def test_not_listed_informational_for_langchain(
    claude_mcp_list: dict[str, MagicMock], capsys: pytest.CaptureFixture[str]
) -> None:
    """Under langchain the "not listed" row doesn't affect the exit code."""
    claude_mcp_list["resolve_llm_method"].return_value = ("langchain", "config.toml")
    with patch(f"{_LC_VERIFY}.verify_langchain", return_value=_langchain_ok()):
        exit_code = _run(["mcp-workspace", "x"])

    assert exit_code == 0
    assert "not listed" in capsys.readouterr().out


def test_parse_receives_resolved_config_and_required_list(
    claude_mcp_list: dict[str, MagicMock],
) -> None:
    """parse_claude_mcp_list gets the required list and mcp_config_resolved."""
    _run(["mcp-workspace", "x"])

    parse: Any = claude_mcp_list["parse_claude_mcp_list"]
    args, kwargs = parse.call_args
    assert args[1] == ["mcp-workspace", "x"]
    assert kwargs["mcp_config_path"] == "/fake/.mcp.json"
    command = claude_mcp_list["execute_command"].call_args.args[0]
    assert command[command.index("--mcp-config") + 1] == "/fake/.mcp.json"
