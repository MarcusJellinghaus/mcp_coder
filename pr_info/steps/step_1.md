# Step 1: `parse_claude_mcp_list()` Parser + `ClaudeMCPStatus` Dataclass

## Context

See [summary.md](summary.md) for full issue context (#748).

This step adds the core parser that runs `claude mcp list` and returns structured connection status results. All subsequent steps depend on this.

## LLM Prompt

> Implement Step 1 of issue #748 (MCP server connection status). Read `pr_info/steps/summary.md` for context and `pr_info/steps/step_1.md` for this step's details. Follow TDD: write tests first in `tests/utils/test_mcp_verification.py`, then implement in `src/mcp_coder/utils/mcp_verification.py`. Run all three code quality checks after changes.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/utils/mcp_verification.py` | Add `ClaudeMCPStatus` dataclass and `parse_claude_mcp_list()` function |
| `tests/utils/test_mcp_verification.py` | Add `TestClaudeMCPStatus` and `TestParseClaudeMcpList` test classes |

## WHAT

### New dataclass

```python
@dataclass(frozen=True)
class ClaudeMCPStatus:
    """Connection status for an MCP server from `claude mcp list`."""
    name: str          # Canonical name from MCP_SERVER_NAMES (e.g. "mcp-tools-py")
    status_text: str   # Raw status text from claude output (e.g. "Connected")
    ok: bool           # True when status_text == "Connected"
```

### New function

```python
def parse_claude_mcp_list(
    env_vars: dict[str, str],
    mcp_config_path: str = ".mcp.json",
    timeout: int = 60,
) -> list[ClaudeMCPStatus] | None:
    """Run `claude mcp list` and parse connection status for known servers.

    Args:
        env_vars: Environment variables for subprocess (for .mcp.json variable resolution).
        mcp_config_path: Path to MCP config file (default: ".mcp.json").
        timeout: Subprocess timeout in seconds (default: 60).

    Returns:
        List of ClaudeMCPStatus for servers in MCP_SERVER_NAMES, or None on any failure.
    """
```

## HOW

### Integration Points

- Uses `find_claude_executable(return_none_if_not_found=True)` from `llm.providers.claude.claude_executable_finder`
- Uses `execute_command()` from `utils.subprocess_runner` (with `env=env_vars`, `timeout_seconds=timeout`)
- Filters results against existing `MCP_SERVER_NAMES` constant
- Name mapping: `claude mcp list` shows `tools-py`, we map to `mcp-tools-py` by prepending `mcp-`

### Imports added to `mcp_verification.py`

```python
import re
from mcp_coder.llm.providers.claude.claude_executable_finder import find_claude_executable
from mcp_coder.utils.subprocess_runner import execute_command
```

## ALGORITHM

```
1. Find claude executable; return None if not found
2. Run: claude --mcp-config <path> --strict-mcp-config mcp list (timeout=60s, env=env_vars)
3. Return None if command fails (non-zero exit, timeout, exception)
4. For each line in stdout, apply regex: ^(\S+):\s+.+\s+-\s+(\S+)\s+(.+)$
5. If regex name (with "mcp-" prefix) is in MCP_SERVER_NAMES → create ClaudeMCPStatus
6. Return list of matched statuses (may be empty if no known servers found)
```

### Regex Details

Sample `claude mcp list` output:
```
Checking MCP server health...

claude.ai Gmail: https://gmail.mcp.claude.com/mcp - ! Needs authentication
tools-py: C:\...\mcp-tools-py.exe --project-dir ... - ✓ Connected
workspace: C:\...\mcp-workspace.exe --project-dir ... - ✓ Connected
```

Regex pattern: `^(\S+):\s+.+\s+-\s+(\S+)\s+(.+)$`
- Group 1: server name (e.g., `tools-py`)
- Group 2: status icon (e.g., `✓`, `✗`, `!`) — captured but not stored
- Group 3: status text (e.g., `Connected`, `Failed to start`)

Name mapping: if `f"mcp-{group1}"` is in `MCP_SERVER_NAMES`, include it.

## DATA

### Input
- `env_vars: dict[str, str]` — passed to subprocess for `.mcp.json` variable resolution
- `mcp_config_path: str` — defaults to `".mcp.json"`
- `timeout: int` — defaults to `60`

### Output
- `list[ClaudeMCPStatus] | None` — `None` means parser could not run (CLI not found, timeout, crash)
- Empty list means CLI ran but no known servers found in output

## TESTS

### `TestClaudeMCPStatus`
- `test_claude_mcp_status_fields` — verify dataclass fields and frozen property
- `test_claude_mcp_status_ok_true_when_connected` — `ok=True` when status_text is "Connected"
- `test_claude_mcp_status_ok_false_when_not_connected` — `ok=False` for other status texts

### `TestParseClaudeMcpList`
- `test_parses_connected_servers` — mock `execute_command` with sample output, verify both servers returned with `ok=True`
- `test_parses_failed_server` — one connected, one failed → verify `ok` flags
- `test_filters_to_known_servers_only` — output includes `claude.ai Gmail` → filtered out
- `test_maps_names_with_mcp_prefix` — `tools-py` in output → `mcp-tools-py` in result
- `test_returns_none_when_claude_not_found` — mock `find_claude_executable` returns None
- `test_returns_none_on_nonzero_exit` — mock execute_command returns non-zero
- `test_returns_none_on_timeout` — mock execute_command with `timed_out=True`
- `test_returns_none_on_exception` — mock execute_command raises exception
- `test_skips_preamble_and_empty_lines` — "Checking MCP server health..." and blank lines don't crash
- `test_unparseable_lines_skipped_gracefully` — malformed lines skipped without error
- `test_env_vars_passed_to_subprocess` — verify env_vars forwarded to execute_command
- `test_mcp_config_path_in_command` — verify `--mcp-config` flag uses provided path
