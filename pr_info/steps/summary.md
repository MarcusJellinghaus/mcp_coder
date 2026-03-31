# Issue #654: icoder timeout, batch files, /exit, UI spacing & colors

## Overview

Five independent enhancements to the iCoder TUI: inactivity timeout for LLM calls,
Windows batch launchers, `/exit` command alias, blank-line spacing between conversation
turns, and Rich-based color coding for different content types.

## Architectural / Design Changes

### Inactivity Timeout (Step 1–3)

**Before:** `stream_subprocess()` uses a single `threading.Timer` — a total-elapsed
timeout that fires once regardless of activity. `RealLLMService` passes no `timeout`
to `prompt_llm_stream()`, defaulting to 30 s. LangChain text streaming has no
inter-chunk timeout. The agent path hardcodes `_AGENT_NO_PROGRESS_TIMEOUT = 600`.

**After:** The timeout semantic becomes **inactivity-based** (reset on each chunk/line):

- `subprocess_streaming.py`: Replace one-shot `Timer` with a **watchdog daemon thread**
  that tracks `last_activity_time` (updated on each yielded line) and kills the process
  when `time.time() - last_activity > timeout`. This is the minimal correct pattern
  because `Timer` objects are not reusable/resettable.
- `langchain/__init__.py` text path: Add `time.time()` check between `chat_model.stream()`
  chunks; raise `TimeoutError` on inactivity gap.
- `langchain/__init__.py` agent path: The existing `q.get(timeout=...)` already IS an
  inactivity timeout by nature (resets on each event). Simply pass the caller's `timeout`
  instead of the hardcoded constant. `_AGENT_NO_PROGRESS_TIMEOUT` is removed.
- `llm_service.py`: New constant `ICODER_LLM_TIMEOUT_SECONDS = 300`, passed through
  to `prompt_llm_stream()`.

**Design rationale:** Inactivity timeout is the natural semantic for streaming — a
process that keeps producing output is healthy; one that goes silent is stuck.
Non-streaming `execute_subprocess` keeps its existing total-timeout behavior unchanged.

### Batch Files (Step 4)

New `icoder.bat` and `icoder_local.bat` follow the identical two-environment pattern
of `claude.bat` / `claude_local.bat`. Only the final launch command differs. No new
architecture — pure duplication of an established pattern.

### /exit Alias (Step 5)

Register a second command pointing to the same handler function. The `CommandRegistry`
decorator returns the original function, so a second `registry.register()` call on
the same function works correctly. One extra line in `quit.py`.

### UI Spacing (Step 6)

Add `output.write("")` blank-line calls in `app.py` at two points: after echoing user
input (before LLM response) and after the LLM stream completes (before next prompt).
No widget changes needed — `RichLog.write("")` produces a blank line.

### UI Color Coding (Step 7)

Add an optional `style` parameter to `OutputLog.append_text()` and
`append_tool_use()`. When provided, wrap content in `rich.text.Text(content, style=...)`
before passing to `RichLog.write()`. The caller (`app.py`) passes style strings:
- User input: `"white on grey23"`
- Tool output: `"white on #0a0a2e"`
- LLM text: `None` (default, no background)

No new classes, no new widgets. Styles are terminal-only (ANSI), no impact on copy/paste.

## Files Modified

| File | Steps | Change |
|------|-------|--------|
| `src/mcp_coder/utils/subprocess_streaming.py` | 1 | Watchdog inactivity timeout |
| `tests/utils/test_subprocess_streaming.py` | 1 | **New** — watchdog timeout tests |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | 2, 3 | Text stream inactivity timeout; agent timeout passthrough |
| `tests/llm/providers/langchain/test_langchain_streaming_timeout.py` | 2, 3 | **New** — inactivity timeout tests |
| `src/mcp_coder/icoder/services/llm_service.py` | 3 | Add constant + pass timeout |
| `tests/icoder/test_llm_service.py` | 3 | Add timeout tests to existing file |
| `icoder.bat` | 4 | **New** — production launcher |
| `icoder_local.bat` | 4 | **New** — dev launcher |
| `src/mcp_coder/icoder/core/commands/quit.py` | 5 | Register `/exit` alias |
| `tests/icoder/test_command_registry.py` | 5 | Add `/exit` tests |
| `src/mcp_coder/icoder/ui/app.py` | 6, 7 | Blank lines + style params |
| `src/mcp_coder/icoder/ui/widgets/output_log.py` | 7 | Optional `style` param |
| `tests/icoder/test_widgets.py` | 6, 7 | Spacing + style tests |
| `tests/icoder/test_app_pilot.py` | 6 | Update expected recorded_lines for spacing |

## Step Sequence

| Step | Topic | Files | Commit |
|------|-------|-------|--------|
| 1 | Subprocess inactivity watchdog | `subprocess_streaming.py`, new test file | Tests + impl |
| 2 | LangChain text stream inactivity timeout | `langchain/__init__.py`, new test file | Tests + impl |
| 3 | LLM service timeout constant + agent timeout passthrough | `llm_service.py`, `langchain/__init__.py`, new test file | Tests + impl |
| 4 | Batch files `icoder.bat` + `icoder_local.bat` | 2 new `.bat` files | New files |
| 5 | `/exit` alias for `/quit` | `quit.py`, `test_command_registry.py` | Tests + impl |
| 6 | UI spacing (blank lines) | `app.py`, `test_widgets.py`, `test_app_pilot.py` | Tests + impl |
| 7 | UI color coding | `output_log.py`, `app.py`, `test_widgets.py` | Tests + impl |
