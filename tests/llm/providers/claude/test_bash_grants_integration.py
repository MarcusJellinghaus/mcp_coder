"""Real-CLI probe: exact ``Bash(...)`` grants allow only the granted commands.

Pins the Claude CLI behaviour ``bash_grants`` relies on: with
``--tools ToolSearch,Bash`` and ``--allowedTools <grants>`` in headless mode,
a granted command runs, while an ungranted command and a granted prefix with
extra arguments are denied (and reported in ``permission_denials``).

Assertions are on side-effects and the result line only, never on model text.
Marked ``claude_cli_integration`` and skipped when ``claude`` is absent.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    build_cli_command,
    format_stream_json_input,
)
from mcp_coder.llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
)
from mcp_coder.utils.subprocess_runner import (
    CommandOptions,
    execute_command,
    execute_subprocess,
)

GRANTS = ["Bash(git config probe.a 1)", "Bash(git config probe.c 3)"]

PROMPT = (
    "Run each of the following shell commands with the Bash tool, one Bash "
    "call per command, in this order. If a command is denied, continue with "
    "the next one. Do not run any other command.\n"
    "1. git config probe.a 1\n"
    "2. git config probe.b 2\n"
    "3. git config probe.a 1 --file extra.cfg\n"
    "4. git config probe.c 3\n"
)


def _git_config_get(repo: Path, key: str) -> str | None:
    """Return the repo-local value of ``key``, or None when unset."""
    result = execute_command(["git", "config", "--local", "--get", key], cwd=str(repo))
    return result.stdout.strip() if result.return_code == 0 else None


def _result_line(stdout: str) -> dict[str, Any]:
    """Return the ``result`` message from NDJSON stdout."""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(msg, dict) and msg.get("type") == "result":
            return msg
    raise AssertionError(f"no result line in output:\n{stdout[-2000:]}")


def _denied_commands(result: dict[str, Any]) -> list[str]:
    """Return the Bash commands listed in ``permission_denials``."""
    commands: list[str] = []
    for denial in result.get("permission_denials") or []:
        tool_input = denial.get("tool_input") if isinstance(denial, dict) else None
        if isinstance(tool_input, dict):
            commands.append(str(tool_input.get("command", "")).strip())
    return commands


@pytest.mark.claude_cli_integration
def test_exact_bash_grants_allow_only_granted_commands(tmp_path: Path) -> None:
    """Granted commands run; ungranted and extended commands are denied."""
    claude_exe = find_claude_executable(return_none_if_not_found=True)
    if claude_exe is None:
        pytest.skip("Claude CLI not installed")

    repo = tmp_path / "repo"
    repo.mkdir()
    assert execute_command(["git", "init"], cwd=str(repo)).return_code == 0

    mcp = tmp_path / "mcp.json"
    mcp.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")

    cmd = build_cli_command(
        None, claude_exe, str(mcp), use_stream_json=True, bash_grants=GRANTS
    )
    result = execute_subprocess(
        cmd,
        CommandOptions(
            cwd=str(repo),
            input_data=format_stream_json_input(PROMPT),
            env_remove=["CLAUDECODE"],
            timeout_seconds=300,
        ),
    )
    assert not result.timed_out, "claude probe timed out"

    # Side-effects: only the exact granted commands ran.
    assert _git_config_get(repo, "probe.a") == "1"
    assert _git_config_get(repo, "probe.c") == "3"
    assert _git_config_get(repo, "probe.b") is None
    assert not (repo / "extra.cfg").exists()

    # The ungranted and the extended command were denied, not skipped.
    denied = _denied_commands(_result_line(result.stdout))
    assert "git config probe.b 2" in denied, denied
    assert "git config probe.a 1 --file extra.cfg" in denied, denied
