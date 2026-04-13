# Issue #777: Escape key to cancel active LLM streaming

## Overview

Add Escape key cancellation of active LLM streaming in the iCoder TUI, and disable the confusing Ctrl+C quit confirmation dialog.

## Architecture / Design Changes

### Cancellation Mechanism

A `threading.Event` (`_cancel_event`) is added to `ICoderApp`. This is checked **between event yields** inside `_stream_llm()`. When set, the loop breaks, which triggers `GeneratorExit` down the generator chain (`app.py` → `app_core.py` → `llm_service.py` → `subprocess_streaming.py`), killing the Claude subprocess. This is the safest approach because:

- No risk of interrupting `store_session()` (it runs **after** the for-loop in `app_core.py:stream_llm()`, so breaking the loop naturally skips it)
- Session ID only updates on `done` events (never received on cancel), so `--continue-session` keeps working with the previous session
- The subprocess kill via `GeneratorExit` is already implemented in `subprocess_streaming.py`

### Key Binding Strategy

- **Escape**: Cancel streaming when busy; no-op when idle. `InputArea._on_key()` already consumes Escape when autocomplete is visible (stops propagation), so only unhandled Escape reaches the App-level binding.
- **Ctrl+C**: Disabled (no-op) to avoid Textual's confusing quit confirmation dialog on Windows.

### Visual Feedback

On cancel: flush any buffered text, append a dim-orange "— Cancelled —" marker, reset the busy indicator. The session is preserved (not reset) — the marker gives Claude context if the user continues.

### No Changes Needed in Lower Layers

- `app_core.py` — generator break skips `store_session()` naturally
- `llm_service.py` — `GeneratorExit` propagates through `yield from`
- `subprocess_streaming.py` — already kills subprocess on `GeneratorExit`
- `input_area.py` — Escape already consumed when autocomplete is visible

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | Add `_cancel_event`, Escape/Ctrl+C bindings, cancel logic in `_stream_llm()`, `STYLE_CANCELLED` constant |
| `tests/icoder/test_app_pilot.py` | Add tests for Escape cancellation and Ctrl+C no-op |

## Implementation Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | Add `STYLE_CANCELLED` constant and `_cancel_event` to `ICoderApp.__init__` |
| [Step 2](step_2.md) | Wire Escape binding + `action_cancel_stream()`, check event in `_stream_llm()`, append cancelled marker |
| [Step 3](step_3.md) | Disable Ctrl+C quit confirmation dialog |
