# Step 2 — `verify` surfaces tool status + count (exit-code-affecting)

**Commit:** `feat: report MCP tools exposed to model in verify`

Implements acceptance items 2 and 5. Depends on Step 1's
`find_exposed_mcp_tools`. See `summary.md`.

## WHERE
- **Impl:** `src/mcp_coder/cli/commands/verify.py`
- **Tests:** `tests/cli/commands/test_verify.py`

## WHAT
New private helper:
```python
def _format_tools_exposed_section(
    system_message: dict[str, Any] | None,
    symbols: dict[str, str],
) -> tuple[list[str], bool | None]:
    """Build the "MCP tools exposed to model" row(s) + exit signal.

    Returns (lines, ok) where ok mirrors the runtime guard:
      True  -> connected with >=1 tool
      None  -> a server is pending (WARN only; never fails the build)
      False -> a server is fatal (failed/unknown) OR connected-but-0-tools
    """
```
Extend the exit-code function signature:
```python
def _compute_exit_code(..., tools_exposed_ok: bool | None = None) -> int:
```

## HOW
- Imports (from the guard, not `utils/`):
  ```python
  from ...llm.providers.claude.claude_mcp_guard import (
      find_exposed_mcp_tools, find_fatal_mcp_servers, find_unavailable_mcp_servers,
  )
  ```
- **Capture the existing test prompt's response** (currently discarded):
  change `prompt_llm("Reply with OK", ...)` to `response = prompt_llm(...)`.
- After the `Test prompt … responded OK` line, when `active_provider == "claude"`:
  ```python
  system_message = response.get("raw_response", {}).get("system")
  lines, tools_exposed_ok = _format_tools_exposed_section(system_message, symbols)
  print("\n".join(lines))
  ```
  Initialise `tools_exposed_ok: bool | None = None` before the `try` so the
  failure path leaves it `None` (neutral).
- Pass `tools_exposed_ok=tools_exposed_ok` into the existing
  `_compute_exit_code(...)` call.
- In `_compute_exit_code`, add (claude-only, mirroring `claude_mcp_ok`):
  ```python
  if active_provider == "claude" and tools_exposed_ok is False:
      return 1
  ```

## ALGORITHM (`_format_tools_exposed_section`)
```
label = "MCP tools exposed to model"
if system_message is None: return ([row(label, WARN, "unavailable (no init event)")], None)
fatal   = find_fatal_mcp_servers(system_message)          # failed/unknown
unavail = find_unavailable_mcp_servers(system_message)    # incl. pending
pending = {k: v for k, v in unavail.items() if k not in fatal}
tools   = find_exposed_mcp_tools(system_message)
names   = [s.get("name") for s in system_message.get("mcp_servers") or [] if s.get("name")]
if fatal:                 marker, ok, value = ERR,  False, f"{len(tools)} ({fatal})"   ; hint = generic
elif pending:             marker, ok, value = WARN, None,  f"{len(tools)} (pending: {sorted(pending)})"
elif not tools:           marker, ok, value = ERR,  False, "0 tools exposed"           ; hint = alwaysLoad
else:                     marker, ok, value = OK,   True,  f"{len(tools)} ({', '.join(names)})"
lines = [row(label, marker, value)] + ([hint_line] if hint else [])
return lines, ok
```
- Hints use the existing `_VALUE_COLUMN_INDENT` + `-> ` style.
  - **alwaysLoad (0-tools only):** `-> server connected but exposed 0 tools; check 'alwaysLoad' in .mcp.json`
  - **generic (fatal):** `-> check the MCP server logs / .mcp.json config`

## DATA
- Row example: `MCP tools exposed to model   [OK]   37 (mcp-tools-py, mcp-workspace)`
- `tools_exposed_ok`: `True | None | False` → only `False` (claude active) forces exit 1.

## TESTS (write first)
`_format_tools_exposed_section` (build `system_message` dicts inline):
- connected + 2 `mcp__*` tools → `[OK]`, ok `True`, names shown.
- connected + `tools: []` → `[ERR]`, ok `False`, line contains `alwaysLoad`.
- one `pending` server → `[WARN]`, ok `None`, no `alwaysLoad` text.
- one `failed` server → `[ERR]`, ok `False`, generic hint (no `alwaysLoad`).
- `None` → `[WARN]`, ok `None`.

`_compute_exit_code`:
- `active_provider="claude", tools_exposed_ok=False` → `1`.
- `tools_exposed_ok=None` → unaffected (existing cases still pass).
- `active_provider="langchain", tools_exposed_ok=False` → not forced to 1 by this rule.

## LLM PROMPT
> Implement Step 2 from `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`). TDD first: add tests to
> `tests/cli/commands/test_verify.py` for `_format_tools_exposed_section`
> (connected+tools, connected+0-tools→alwaysLoad hint, pending→WARN,
> failed→generic hint, None) and for the new `tools_exposed_ok` branch of
> `_compute_exit_code`. Then edit `verify.py`: import the three guard readers,
> capture the existing `"Reply with OK"` response, print the tools-exposed
> row(s) for the claude provider, and thread `tools_exposed_ok` into
> `_compute_exit_code` (connected→OK, pending→WARN, fatal/0-tools→exit 1). Put
> the `alwaysLoad` hint ONLY in the 0-tools branch. Run pylint/pytest
> (`-n auto`, integration-excluded)/mypy, fix all, format, single commit.
