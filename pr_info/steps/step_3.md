# Step 3: Verify Command — Claude MCP Section + Provider-Aware Display + Exit Code

## Context

See [summary.md](summary.md) for full issue context (#748).

This step updates `mcp-coder verify` to show provider-aware MCP sections. Active provider's section shown first; other provider's section labeled "for completeness". Claude MCP failures = hard failure (exit 1) only when Claude is the active provider.

## LLM Prompt

> Implement Step 3 of issue #748 (MCP server connection status). Read `pr_info/steps/summary.md` for context and `pr_info/steps/step_3.md` for this step's details. Steps 1-2 are already implemented — `ClaudeMCPStatus`, `parse_claude_mcp_list()` exist in `utils/mcp_verification.py`, and `RuntimeInfo.mcp_connection_status` is wired. Follow TDD: write tests first, then implement. Run all three code quality checks after changes.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/verify.py` | Add `_format_claude_mcp_section()`, update `execute_verify()`, update `_compute_exit_code()` |
| `tests/cli/commands/test_verify_format_section.py` | Add `TestFormatClaudeMcpSection` test class |
| `tests/cli/commands/test_verify_exit_codes.py` | Add tests for `claude_mcp_ok` parameter |
| `tests/cli/commands/test_verify_command.py` | Add integration test for provider-aware MCP sections |

## WHAT

### New function

```python
def _format_claude_mcp_section(
    statuses: list[ClaudeMCPStatus],
    symbols: dict[str, str],
    *,
    for_completeness: bool = False,
) -> str:
    """Format MCP server connection status from `claude mcp list`.

    Args:
        statuses: Parsed connection statuses.
        symbols: Dict with 'success', 'failure' keys.
        for_completeness: If True, append "for completeness" to section title.

    Returns:
        Formatted multi-line string.
    """
```

### Updated function signature

```python
def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
    test_prompt_ok: bool = True,
    mcp_result: dict[str, Any] | None = None,
    config_has_error: bool = False,
    claude_mcp_ok: bool | None = None,  # NEW
) -> int:
```

### `execute_verify()` changes

After resolving `active_provider` and `mcp_config_resolved`, call `parse_claude_mcp_list()` and display both MCP sections in provider-dependent order.

## HOW

### Imports added to `verify.py`

```python
from ...utils.mcp_verification import ClaudeMCPStatus, parse_claude_mcp_list
from ...llm.env import prepare_llm_environment
```

### `_format_claude_mcp_section()` output format

```
=== MCP SERVERS (via Claude Code) ===
  mcp-tools-py         ✓ Connected
  mcp-workspace        ✗ Failed to start
```

With `for_completeness=True`:
```
=== MCP SERVERS (via Claude Code — for completeness) ===
  ...
```

### Provider-aware section ordering in `execute_verify()`

**When provider = claude:**
1. Claude MCP section (primary) — `for_completeness=False`
2. LangChain MCP section — title changed to include "for completeness" (only if available)

**When provider = langchain:**
1. LangChain MCP section (primary) — existing `_format_mcp_section()`, unchanged
2. Claude MCP section — `for_completeness=True` (only if available)

### Exit code logic addition

In `_compute_exit_code()`:
```python
# Claude MCP failures affect exit code when claude is active
if active_provider == "claude" and claude_mcp_ok is False:
    return 1
```

`claude_mcp_ok` values:
- `None` — parser couldn't run. When Claude is active: this is a hard failure (exit 1). When langchain: ignored.
- `True` — all known servers connected
- `False` — at least one known server not connected

**Decision 12 from issue**: If `claude mcp list` itself fails (CLI not found, timeout, crash), hard failure (exit 1) when Claude is the active provider. This means `parse_claude_mcp_list` returning `None` when Claude is active → exit 1.

## ALGORITHM

### `_format_claude_mcp_section()`

```
1. Build title: "MCP SERVERS (via Claude Code)" + optional "— for completeness"
2. For each status in statuses:
3.   symbol = success if status.ok else failure
4.   Append line: "  {name:<20s} {symbol} {status_text}"
5. Return joined lines
```

### `execute_verify()` MCP section logic

```
1. Compute env_vars via prepare_llm_environment(project_dir)
2. claude_mcp = parse_claude_mcp_list(env_vars) if mcp_config_resolved else None
3. If active_provider == "claude":
   a. Print claude MCP section (primary)
   b. Print langchain MCP section (for completeness, if available)
4. If active_provider == "langchain":
   a. Print langchain MCP section (primary) — existing code
   b. Print claude MCP section (for completeness, if available)
5. Compute claude_mcp_ok:
   - None if claude_mcp is None
   - True if all statuses have ok=True
   - False otherwise
6. Pass claude_mcp_ok to _compute_exit_code()
```

### `_compute_exit_code()` addition

```
1. Existing checks (config_has_error, test_prompt_ok, provider checks, mcp langchain)
2. NEW: if active_provider == "claude" and claude_mcp_ok is not True:
   (covers both False and None per Decision 12)
   return 1
```

## DATA

### `_format_claude_mcp_section()` input/output
- Input: `list[ClaudeMCPStatus]`, `dict[str, str]` symbols, `for_completeness: bool`
- Output: formatted multi-line string

### `_compute_exit_code()` new parameter
- `claude_mcp_ok: bool | None = None`
  - `None` → parser failed (hard failure when Claude active, ignored otherwise)
  - `True` → all servers connected
  - `False` → at least one server not connected

### Existing `_format_mcp_section()` title change
When rendered "for completeness", change section title from:
```
=== MCP SERVERS (via langchain-mcp-adapters) ===
```
to:
```
=== MCP SERVERS (via langchain-mcp-adapters — for completeness) ===
```

This requires a small update to `_format_mcp_section()` to accept a `for_completeness` keyword.

## TESTS

### `tests/cli/commands/test_verify_format_section.py` — new `TestFormatClaudeMcpSection`

- `test_connected_servers_show_success_symbol` — two connected → both show `[OK] Connected`
- `test_failed_server_shows_failure_symbol` — one failed → shows `[NO] Failed to start`
- `test_section_title_default` — title is `"MCP SERVERS (via Claude Code)"`
- `test_section_title_for_completeness` — `for_completeness=True` → title includes `"for completeness"`
- `test_server_names_left_aligned` — verify `{name:<20s}` alignment

### `tests/cli/commands/test_verify_exit_codes.py` — additions to `TestComputeExitCode`

- `test_claude_active_mcp_ok_exit_0` — `claude_mcp_ok=True` → exit 0
- `test_claude_active_mcp_fail_exit_1` — `claude_mcp_ok=False` → exit 1
- `test_claude_active_mcp_none_exit_1` — `claude_mcp_ok=None` when active=claude → exit 1 (Decision 12)
- `test_langchain_active_mcp_fail_no_effect` — `claude_mcp_ok=False` when active=langchain → exit 0
- `test_langchain_active_mcp_none_no_effect` — `claude_mcp_ok=None` when active=langchain → exit 0

### `tests/cli/commands/test_verify_command.py` — integration tests

- `test_claude_provider_shows_claude_mcp_section_first` — mock everything, verify "via Claude Code" appears before "via langchain-mcp-adapters"
- `test_langchain_provider_shows_langchain_section_first` — verify "via langchain-mcp-adapters" appears before "via Claude Code"
- `test_claude_mcp_section_shows_for_completeness_when_langchain_active` — verify "for completeness" label
- `test_claude_mcp_failure_when_not_active_does_not_exit_1` — verify exit code 0 when claude MCP fails but langchain is active
