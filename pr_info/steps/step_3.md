# Step 3: Wire `/clear` → session reset in AppCore

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.
> **Depends on:** Step 1 (`reset_session` flag on `Response`) and Step 2 (`reset_session()` on `LLMService`).

## Goal

1. Update `/clear` handler to return `Response(clear_output=True, reset_session=True)`.
2. Update `AppCore.handle_input()` to act on the `reset_session` flag — call `self._llm_service.reset_session()` and emit a `"session_reset"` event.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/core/commands/clear.py` | Modify — add `reset_session=True` |
| `src/mcp_coder/icoder/core/app_core.py` | Modify — handle `reset_session` flag |
| `tests/icoder/test_app_core.py` | Modify — add integration tests |

## WHAT

### `clear.py` — handler change

```python
return Response(clear_output=True, reset_session=True)
```

### `app_core.py` — `handle_input()` addition

After the existing command dispatch block, before returning the response:

```python
if response.reset_session:
    self._llm_service.reset_session()
    self._event_log.emit("session_reset")
```

## HOW

- `clear.py`: One-line change — add keyword argument.
- `app_core.py`: Add 3 lines after command dispatch, before `return response`. No new imports needed — `LLMService` already imported, `reset_session()` added in Step 2.

## ALGORITHM (pseudocode for `handle_input` change)

```
response = registry.dispatch(text)
if response is not None:
    emit("command_matched", ...)
    if response.text: emit("output_emitted", ...)
    if response.reset_session:          # NEW
        llm_service.reset_session()     # NEW
        emit("session_reset")           # NEW
    return response
```

## DATA

- `"session_reset"` event: no extra data fields (just the event name + timestamp)
- `/clear` response: `Response(clear_output=True, reset_session=True)`

## Tests (TDD — write first)

### `test_app_core.py` — add two tests:

1. **`test_clear_resets_session`** — Create a `FakeLLMService` with canned responses that include a `done` event carrying a `session_id` (following the pattern in `test_fake_session_id_from_done`). Stream to populate the session_id, then call `/clear`, and assert `llm_service.session_id is None`.

2. **`test_clear_emits_session_reset_event`** — Call `/clear`, assert `event_log.entries` contains an entry with `event == "session_reset"`.

### Update existing test

- **`test_handle_clear`** — Also assert `response.reset_session is True` alongside the existing `clear_output` check (consolidate into one test, no separate flag test needed).

## Commit

```
feat(icoder): /clear resets LLM session (#765)
```

## LLM Prompt

```
Implement Step 3 from pr_info/steps/step_3.md (see pr_info/steps/summary.md for context).

Update /clear handler in clear.py to set reset_session=True.
Update AppCore.handle_input() in app_core.py to call llm_service.reset_session() and emit "session_reset" event when the flag is set.
Add tests in test_app_core.py. Run all code quality checks. Commit when green.
```
