# Step 3: Disable Ctrl+C quit confirmation dialog

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3: Disable Textual's default Ctrl+C quit confirmation dialog by adding a no-op binding. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- `src/mcp_coder/icoder/ui/app.py` — add Ctrl+C binding
- `tests/icoder/test_app_pilot.py` — add test

## WHAT

### Add Ctrl+C no-op binding

```python
class ICoderApp(App[None]):
    BINDINGS = [
        Binding("escape", "cancel_stream", "Cancel", show=False),
        Binding("ctrl+c", "no_op", "Copy", show=False),
    ]
```

Textual's built-in `no_op` action exists — no method needed.

## HOW

- Add the `Binding("ctrl+c", "no_op", "Copy", show=False)` entry to the existing `BINDINGS` list (created in Step 2)

## TESTS

### Test: Ctrl+C does not quit the app

```python
async def test_ctrl_c_does_not_quit(icoder_app):
    """Ctrl+C should not trigger the quit confirmation dialog."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert icoder_app.is_running
```

## DATA

- No new data structures
- No return values
- Side effect: Ctrl+C is silently consumed instead of showing quit dialog
