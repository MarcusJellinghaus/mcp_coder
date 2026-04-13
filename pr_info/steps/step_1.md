# Step 1: Show "Querying LLM..." on submit (test + implementation)

> **Reference:** [summary.md](summary.md) — Issue #779

## LLM Prompt

```
Implement issue #779: Add show_busy("Querying LLM...") in ICoderApp before run_worker().
See pr_info/steps/summary.md for context and pr_info/steps/step_1.md for details.
Run all code quality checks after changes. This step produces one commit.
```

## WHERE

| File | Action |
|------|--------|
| `tests/icoder/test_app_pilot.py` | Add one test |
| `src/mcp_coder/icoder/ui/app.py` | Add one line |

## WHAT — Test

Add `test_busy_indicator_shows_querying_on_submit` to `tests/icoder/test_app_pilot.py`:

```python
async def test_busy_indicator_shows_querying_on_submit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After submitting LLM input, indicator immediately shows 'Querying LLM...' before stream starts."""
```

**Signature:** `async def test_busy_indicator_shows_querying_on_submit(make_icoder_app) -> None`

### Algorithm (test)

```
1. Create a threading.Event (starts unset)
2. Define SlowLLMService in the test file (same pattern as ErrorAfterChunksLLMService)
   — its stream() method waits on the event before yielding any stream events
3. Create app with SlowLLMService via make_icoder_app
4. Submit input via pilot
5. await pilot.pause() to let the worker start and show_busy() execute
6. Read BusyIndicator.label_text and assert "Querying LLM..." is in the label
7. Set the event to unblock SlowLLMService.stream()
8. await pilot.pause() to let the worker complete and the indicator reset
9. Assert indicator shows "✓ Ready"
```

### Data

- Uses `make_icoder_app` fixture with a custom `SlowLLMService` (blocking iterator using `threading.Event`)
- `SlowLLMService` follows the same pattern as `ErrorAfterChunksLLMService` already defined in `tests/icoder/test_app_pilot.py`
- Asserts on `BusyIndicator.label_text` string content

## WHAT — Implementation

In `ICoderApp.on_input_area_input_submitted`, add one line in the `send_to_llm` branch:

```python
elif response.send_to_llm:
    output.write("")
    llm_input = response.llm_text or text
    self.query_one(BusyIndicator).show_busy("Querying LLM...")  # <-- NEW
    self.run_worker(lambda: self._stream_llm(llm_input), thread=True)
```

### HOW — Integration

- No new imports needed (`BusyIndicator` is already imported)
- No new methods or classes
- Existing stream event handlers progressively update the message ("Thinking...", tool name, "✓ Ready")

### Algorithm (implementation)

```
1. Query BusyIndicator widget
2. Call show_busy("Querying LLM...")
3. (existing) run_worker starts _stream_llm in background thread
```

### DATA

- Input: None (uses existing `BusyIndicator` instance)
- Output: Side effect — widget updates its label to show spinner + "Querying LLM..." + elapsed time

## Commit

```
fix(icoder): show busy indicator immediately on LLM submit (#779)

Add show_busy("Querying LLM...") before run_worker() so the user
sees feedback immediately instead of stale "✓ Ready" while the
LLM request is in flight.
```
