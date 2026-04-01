# Step 3: Wire history.add() in ICoderApp Submit Handler

> **Reference**: See `pr_info/steps/summary.md` for full context. Steps 1-2 must be completed first.

## Goal

Connect the final wire: when user submits input, add it to `InputArea`'s history. This is a one-line change in `app.py`.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | **MODIFY** — add `history.add()` call |

## WHAT — Change to `ICoderApp.on_input_area_input_submitted()`

Add one line at the start of the handler, after extracting `text`:

```python
def on_input_area_input_submitted(self, message: InputArea.InputSubmitted) -> None:
    """Handle submitted input: route through AppCore."""
    text = message.text
    self.query_one(InputArea).history.add(text)  # <-- NEW LINE
    output = self.query_one(OutputLog)
    # ... rest unchanged
```

## ALGORITHM

```
on_submit(text):
    input_area.history.add(text)    # <-- this is the only new line
    # ... existing routing logic unchanged
```

## DATA — No New Types or Structures

Calls existing `CommandHistory.add()` API on `InputArea.history` attribute (added in Step 2).

## HOW — Integration Points

- No new imports needed (`InputArea` is already imported in `app.py`)
- Accesses `InputArea.history` attribute created in Step 2
- Placement: immediately after `text = message.text`, before `output = ...`

## Verification

- Existing `tests/icoder/test_app_pilot.py` tests should continue passing (no behavior change for existing flows)
- The widget key tests from Step 2 already test the full round-trip by calling `history.add()` directly
- Run all three code quality checks to confirm

## LLM Prompt

```
Implement Step 3 of issue #631 (iCoder command history).
See pr_info/steps/summary.md for full context and pr_info/steps/step_3.md for this step's spec.

1. Add the history.add(text) call to on_input_area_input_submitted() in src/mcp_coder/icoder/ui/app.py
2. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
3. Commit when all checks pass
```
