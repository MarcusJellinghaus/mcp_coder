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
1. Create app with SlowLLMService that blocks before yielding events
2. Submit input via pilot
3. While worker is running (before stream events arrive), read BusyIndicator.label_text
4. Assert "Querying LLM..." is in the label
5. Unblock the LLM service, let stream complete
6. Assert indicator returns to "✓ Ready"
```

### Data

- Uses `make_icoder_app` fixture with a custom `SlowLLMService` (blocking iterator using `threading.Event`)
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
