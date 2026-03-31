# Step 6: UI Spacing — Blank Lines Between Conversation Turns

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Add blank lines between conversation sections for readability:
- One blank line after user input (before LLM response)
- One blank line after LLM response completes (before next input)

## WHERE

- **Modify:** `src/mcp_coder/icoder/ui/app.py`

## WHAT

### `app.py` — Add blank lines at two points

**Point 1:** In `on_input_area_input_submitted()`, after echoing user input and
before LLM streaming starts:

```python
def on_input_area_input_submitted(self, message: InputArea.InputSubmitted) -> None:
    text = message.text
    output = self.query_one(OutputLog)
    output.append_text(f"> {text}")
    # ... existing routing ...
    elif response.send_to_llm:
        output.write("")           # blank line after user input
        self.run_worker(...)
```

**Point 2:** In `_stream_llm()`, after the streaming loop completes:

```python
def _stream_llm(self, text: str) -> None:
    try:
        for event in self._core.stream_llm(text):
            self.call_from_thread(self._handle_stream_event, event)
        self.call_from_thread(self._append_blank_line)  # blank line after LLM response
    except Exception as exc:
        self.call_from_thread(self._show_error, str(exc))
```

Add helper:
```python
def _append_blank_line(self) -> None:
    self.query_one(OutputLog).write("")
```

**Note:** Use `output.write("")` directly (not `append_text("")`) so blank lines
don't pollute the `_recorded` buffer used for testing. Tests check `recorded_lines`
for content, not spacing.

## HOW

- `RichLog.write("")` produces a visual blank line in the TUI.
- `_append_blank_line()` is a tiny helper to allow `call_from_thread` (which needs a callable).
- No changes to `OutputLog` widget.

## ALGORITHM

No algorithm — two `write("")` calls at specific points.

## DATA

No new types or data structures.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md for full context.

Implement step 6: Add blank lines between conversation turns in app.py. Add
output.write("") after user input echo (before LLM call) and after LLM stream
completes. Use write("") not append_text("") so recorded_lines aren't affected.
Verify existing tests still pass. Run all three MCP code quality checks after changes.
Commit message: "icoder: blank line spacing between conversation turns"
```
