# Step 2 — Show the `Logs:` section in `/info`

> Read `pr_info/steps/summary.md` first for the overall goal, design rationale,
> and the KISS divergence from the issue's `AppCore` routing decision.
> Depends on **Step 1** (`EventLog.logs_dir`).

## Goal

Render a `Logs:` section in `/info` showing the current session's log file and
the logs directory, placed **between** the `MCP_CODER_* env vars` and
`Other env vars` sections. Wire the `EventLog` into `register_info` by adding a
single `event_log` parameter (no `AppCore` routing).

Target output:

```
Logs:
  Current: C:\project\logs\icoder_2026-04-17T10-30-00.jsonl
  Directory: C:\project\logs
```

Bare paths, no trailing separator on the directory.

## WHERE

- Source: `src/mcp_coder/icoder/core/commands/info.py`
- Source: `src/mcp_coder/cli/commands/icoder.py` (call-site wiring)
- Test:   `tests/icoder/test_info_command.py`

## WHAT — signatures

In `info.py`:

```python
def _format_info(
    runtime_info: RuntimeInfo,
    mcp_manager: MCPManager | None,
    event_log: EventLog,
) -> str: ...


def register_info(
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
    event_log: EventLog,
    mcp_manager: MCPManager | None = None,
) -> None: ...
```

`register_info` passes `event_log` through to `_format_info` in its closure:

```python
OutputText(text=_format_info(runtime_info, mcp_manager, event_log))
```

Add the `EventLog` import under the existing `TYPE_CHECKING` block in `info.py`:

```python
if TYPE_CHECKING:
    ...
    from mcp_coder.icoder.core.event_log import EventLog
```

## HOW (integration) — `icoder.py` wiring

Current state: `register_info(registry, runtime_info, mcp_manager=mcp_manager)`
is called at module line ~139, **before** `AppCore` / `EventLog` exist.

Change:

1. **Remove** that early `register_info(...)` call (the one near the
   `register_skill_commands` block).
2. **Add** the call **inside** the `with EventLog(logs_dir=...) as event_log:`
   block, next to `register_color(registry, app_core)` /
   `register_display(registry, app_core)`:

   ```python
   register_info(registry, runtime_info, event_log, mcp_manager=mcp_manager)
   register_color(registry, app_core)
   register_display(registry, app_core)
   ```

   `runtime_info` and `mcp_manager` are already in scope; `event_log` is the
   `with` target. Safe because no command runs until the REPL loop starts
   (also inside the `with` block).

Do **not** modify `AppCore`.

## ALGORITHM — `Logs:` section in `_format_info`

Insert immediately after the `MCP_CODER_* env vars` block and before the
`Other env vars` block:

```
append ""                                        # blank separator line
append "Logs:"
append "  Current: {event_log.current_path}"     # f-string, bare path
append "  Directory: {event_log.logs_dir}"       # bare, no trailing sep
```

`str(Path)` renders without a trailing separator, matching other paths in
`/info`.

## DATA

- `event_log.current_path` → `Path` to the active `icoder_*.jsonl` file.
- `event_log.logs_dir` → `Path` to the logs directory.
- `_format_info` returns the full multi-line `str` (unchanged contract).

## TDD — test updates in `test_info_command.py`

All `register_info(...)` call sites gain an `event_log` argument. The existing
`conftest.py` provides an `event_log` fixture (writes to `tmp_path`) — add
`event_log: EventLog` to the parameters of each affected test and pass it.

1. **Import** the fixture type at the top:
   `from mcp_coder.icoder.core.event_log import EventLog`.

2. **Update ~12 call sites**, e.g.:
   - `register_info(registry, runtime_info)`
     → `register_info(registry, runtime_info, event_log)`
   - `register_info(registry, runtime_info, mcp_manager=mock_manager)`
     → `register_info(registry, runtime_info, event_log, mcp_manager=mock_manager)`
   - `register_info(registry, runtime_info, mcp_manager=None)`
     → `register_info(registry, runtime_info, event_log, mcp_manager=None)`
   Add `event_log: EventLog` to each of those test function signatures so the
   fixture is injected.

3. **New test** for the section (place with the other `/info` integration
   tests):

   ```python
   @patch(
       "mcp_coder.icoder.core.commands.info.find_claude_executable",
       return_value=None,
   )
   def test_info_shows_logs_section(
       _mock_claude: object,
       registry: CommandRegistry,
       runtime_info: RuntimeInfo,
       event_log: EventLog,
   ) -> None:
       register_info(registry, runtime_info, event_log)
       result = registry.dispatch("/info")
       text = _info_text(result)
       assert "Logs:" in text
       assert f"Current: {event_log.current_path}" in text
       assert f"Directory: {event_log.logs_dir}" in text
   ```

4. **Optional placement guard** (keeps the section anchored per Decision #5):

   ```python
       assert text.index("MCP_CODER_* env vars:") < text.index("Logs:")
       assert text.index("Logs:") < text.index("Other env vars")
   ```

`tests/icoder/test_cli_icoder.py::test_info_command_registered_in_icoder`
requires **no change** — it only asserts `/info` is registered after
`execute_icoder`, and the wiring move keeps it green.

## Definition of done (one commit)

1. Update tests first (signatures fail against the old `register_info`).
2. Change `_format_info` + `register_info` in `info.py`.
3. Move the `register_info` call in `icoder.py` into the `with` block and pass
   `event_log`.
4. Run and pass all three MCP checks:
   - `mcp__mcp-tools-py__run_pylint_check`
   - `mcp__mcp-tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__mcp-tools-py__run_mypy_check`
5. Run `./tools/format_all.sh`, then commit tests + implementation together.

## Commit message

```
Show iCoder log file path and logs dir in /info (#764)
```
