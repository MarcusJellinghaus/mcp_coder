# Step 2: Disable Ctrl+C quit confirmation dialog

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: Disable Textual's default Ctrl+C quit confirmation dialog by adding a custom no-op action and binding. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- `src/mcp_coder/icoder/ui/app.py` — add Ctrl+C binding and `action_noop()` method
- `tests/icoder/test_app_pilot.py` — add test

## WHAT

### Add Ctrl+C binding with custom action

Textual does not have a built-in `no_op` action. Use a custom action name and define the method.

```python
class ICoderApp(App[None]):
    BINDINGS = [
        Binding("escape", "cancel_stream", "Cancel", show=False),
        Binding("ctrl+c", "noop", "Copy", show=False),
    ]

    def action_noop(self) -> None:
        """Suppress Ctrl+C quit dialog."""
```

## HOW

- Add the `Binding("ctrl+c", "noop", "Copy", show=False)` entry to the existing `BINDINGS` list (created in Step 1)
- Add `action_noop()` method to `ICoderApp`

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
        # Verify no quit-related notification appeared
        assert len(icoder_app._notifications) == 0
```

## DATA

- No new data structures
- No return values
- Side effect: Ctrl+C is silently consumed instead of showing quit dialog
