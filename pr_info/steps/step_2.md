# Step 2 — `provider` field in `session_start`; remove `session_reset`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_2.md`) with strict TDD. Update tests first, then
> the production code. Run pylint, pytest, mypy via the mandatory MCP
> tools and ensure all pass. Single commit.

## WHERE

- Modify: `src/mcp_coder/cli/commands/icoder.py` — add `provider=...` to
  the `event_log.emit("session_start", ...)` call.
- Modify: `src/mcp_coder/icoder/core/app_core.py` — remove the
  `event_log.emit("session_reset")` call from the command-dispatch path
  (lines around the `response.reset_session` block).
- Update tests:
  - `tests/icoder/test_cli_icoder.py` — assert `session_start` payload
    contains `provider`.
  - `tests/icoder/test_app_core.py` — remove (or invert) the assertion
    that `/clear` emits `session_reset`.

## WHAT

In `cli/commands/icoder.py`:

```python
event_log.emit(
    "session_start",
    provider=provider,                      # NEW
    mcp_coder_version=runtime_info.mcp_coder_version,
    tool_env=runtime_info.tool_env_path,
    project_venv=runtime_info.project_venv_path,
    project_dir=runtime_info.project_dir,
    mcp_servers={...},
    mcp_connection_status={...},
)
```

In `app_core.handle_input()` — remove:

```python
if response.reset_session:
    self._llm_service.reset_session()
    self._event_log.emit("session_reset")   # ← delete this line
```

(Step 4 will replace the deleted line with a `rotate()` call. Keeping
this step minimal: just remove the now-stale event emission.)

## HOW

- `provider` is already in scope in `execute_icoder()` from
  `parse_llm_method_from_args(llm_method)`. Pass it directly.
- The order of kwargs is irrelevant for JSON output.

## ALGORITHM

N/A — small additive/removal edits.

## DATA

`session_start` event payload now includes:
- `provider: str` — `"claude"`, `"copilot"`, `"langchain"`, etc.

`session_reset` event is no longer present in any log written by this
codebase (still parseable if found in old logs — replay/inventory simply
ignore unknown event types).

## Test Cases

1. CLI test: invoke `execute_icoder` with mocked components in `tmp_path`,
   read the produced JSONL, parse the first line, assert `event ==
   "session_start"` and `provider == <expected>`.
2. AppCore test: dispatch `/clear`, read the emitted events from
   `event_log.entries`, assert that no entry has
   `event == "session_reset"`.
3. AppCore test: confirm `_llm_service.reset_session()` is still invoked
   on `/clear` (existing behaviour preserved).

## Out of Scope

- Log rotation on `/clear` — Step 4.
- Picker provider filtering — Step 7.
