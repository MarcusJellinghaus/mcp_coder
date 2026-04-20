# Step 1: Add `has_error` property to `ResponseAssembler`

> **Context**: See [summary.md](summary.md) for full issue context.

## Goal

Expose whether the assembler received an error event, so downstream code (prompt command) can check without reaching into `raw_response` internals.

## WHERE

- **Production**: `src/mcp_coder/llm/types.py` — `ResponseAssembler` class
- **Tests**: `tests/llm/test_types.py`

## WHAT

Add a read-only property to `ResponseAssembler`:

```python
@property
def has_error(self) -> bool:
    """Whether an error event was received during streaming."""
    return self._error is not None
```

## HOW

- Add the property after the existing `add()` method, before `result()`
- No new imports needed
- No changes to existing methods

## ALGORITHM

```
1. ResponseAssembler already stores _error: str | None = None
2. add() already sets _error on error events (line 120-123)
3. Add @property has_error -> bool: return self._error is not None
```

## DATA

- Input: none (reads existing `_error` field)
- Output: `bool` — `True` if any error event was added, `False` otherwise

## Tests (write first)

Add to `tests/llm/test_types.py`:

1. **`test_response_assembler_has_error_false_initially`** — new assembler → `has_error` is `False`
2. **`test_response_assembler_has_error_true_after_error_event`** — add error event → `has_error` is `True`
3. **`test_response_assembler_has_error_false_without_error`** — add text_delta + done events → `has_error` is `False`

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md.
Read pr_info/steps/summary.md for full context.

Add a `has_error` property to `ResponseAssembler` in `src/mcp_coder/llm/types.py`.
Write tests first in `tests/llm/test_types.py`, then implement the property.
Run all three code quality checks after changes.
```
