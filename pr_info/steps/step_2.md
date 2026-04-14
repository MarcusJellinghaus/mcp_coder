# Step 2: Wire TokenUsage into AppCore

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #808).

## Goal

Add `TokenUsage` to `AppCore` and update `stream_llm()` to populate it from the assembler's usage data after each LLM stream. Test-driven.

## LLM Prompt

```
Implement Step 2 of Issue #808 (see pr_info/steps/summary.md for context).

Wire TokenUsage into AppCore: add _token_usage field, expose property,
update stream_llm() to extract usage from assembler.result().
Add tests to tests/icoder/test_app_core.py.
Follow TDD: write tests first, then implementation.
Run all three code quality checks after changes.
```

## WHERE

- **Modify**: `src/mcp_coder/icoder/core/app_core.py`
- **Modify**: `tests/icoder/test_app_core.py`

## WHAT

### Changes to `AppCore.__init__`
```python
from mcp_coder.icoder.core.types import Response, TokenUsage
# ...
self._token_usage = TokenUsage()
```

### New property
```python
@property
def token_usage(self) -> TokenUsage:
    """Cumulative token usage for this session."""
    return self._token_usage
```

### Changes to `AppCore.stream_llm()`

After the existing `response_data = assembler.result()` and `store_session(...)` lines, extract usage:

```python
usage = response_data["raw_response"].get("usage", {})
if isinstance(usage, dict):
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        self._token_usage.update(input_tokens, output_tokens)
```

## HOW

- Import `TokenUsage` from `mcp_coder.icoder.core.types`
- Insert usage extraction after the existing `store_session()` call — minimal diff
- Defensive type checks: usage dict may be absent (LangChain) or malformed

## ALGORITHM

```
# After existing stream loop and store_session():
raw = assembler.result()["raw_response"]
usage = raw.get("usage", {})
input_t = usage.get("input_tokens", 0)  # default 0 if missing
output_t = usage.get("output_tokens", 0)
if both are int: self._token_usage.update(input_t, output_t)
```

## DATA

- `app_core.token_usage` → `TokenUsage` instance (always available)
- After streaming with `{"type": "done", "usage": {"input_tokens": 100, "output_tokens": 50}}`:
  - `token_usage.last_input` → `100`
  - `token_usage.total_input` → `100`
- After streaming with `{"type": "done"}` (no usage):
  - `token_usage` unchanged (update not called)

### Tests to write (in `test_app_core.py`)

1. `test_token_usage_initial_state` — `app_core.token_usage` exists, all zeros, `has_data` False
2. `test_stream_llm_updates_token_usage` — use `FakeLLMService` with `{"type": "done", "usage": {"input_tokens": 100, "output_tokens": 50}}`, verify `token_usage.last_input == 100`, `total_input == 100`
3. `test_stream_llm_cumulative_tokens` — two streams with usage, verify totals accumulate
4. `test_stream_llm_no_usage_data` — stream with `{"type": "done"}` (no usage key), verify `token_usage.has_data` remains False

### Test fixture note

The existing `conftest.py` patches `store_session`. The `FakeLLMService` default response is `[{"type": "text_delta", "text": "fake response"}, {"type": "done"}]` — no usage. Tests needing usage must provide custom responses.
