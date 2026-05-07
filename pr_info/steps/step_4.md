# Step 4 — `AppCore` rotates log on `reset_session=True`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_4.md`) with strict TDD. Tests first, then code.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Modify: `src/mcp_coder/icoder/core/app_core.py`
- Update tests: `tests/icoder/test_app_core.py`

## WHAT

In `AppCore.handle_input()`:

```python
if response.reset_session:
    self._llm_service.reset_session()
    self._event_log.rotate()      # NEW — replaces the removed session_reset emit
```

No new public surface. No new dataclass field on `Response`.

## HOW

- Relies on `EventLog.rotate()` from Step 1.
- `/clear` is the only built-in command that sets `reset_session=True`,
  so binding rotation to that flag is precise.
- The new conversation gets its own log file with its own
  `session_start`-less prefix; **no** `session_start` is re-emitted by
  this step. Any future need for a fresh `session_start` line is up to
  the caller (CLI re-emits it on startup; mid-run rotation simply
  doesn't have one — picker uses the first `input_received` for date in
  that case via `os.path.getmtime`-style fallback if needed; see Step 7).

## ALGORITHM

```
handle_input(text):
    ...
    response = registry.dispatch(text)
    if response is not None:
        emit("command_matched", ...)
        if response.text: emit("output_emitted", text=response.text)
        if response.reset_session:
            llm_service.reset_session()
            event_log.rotate()         # NEW
        return response
    ...
```

## DATA

No new types. `Response` unchanged.

## Test Cases

1. With a real `EventLog` in `tmp_path` and a `FakeLLMService`:
   - record the initial `event_log.current_path`
   - dispatch `/clear`
   - assert `event_log.current_path` differs from the initial path
   - assert two `icoder_*.jsonl` files now exist in `tmp_path`
2. After `/clear`, an `emit("input_received", text="x")` writes to the
   new file (read both files; the new file contains the entry, the old
   one does not).
3. After `/clear`, `_llm_service.session_id is None` (regression check
   that `reset_session()` is still called).
4. Non-resetting commands (e.g. `/help`) do **not** rotate the log
   (`current_path` unchanged after dispatching `/help`).

## Out of Scope

- Picker / inventory handling of mid-rotation logs — Step 7 design
  note: inventory uses `session_start` when present, falls back to file
  mtime otherwise.
