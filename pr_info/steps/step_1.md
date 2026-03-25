# Step 1: Remove `ask_llm()` and Migrate Callers to `prompt_llm()`

## Context

See `pr_info/steps/summary.md` for full context. This is step 1 of 6 for issue #551.

`ask_llm()` is a thin wrapper around `prompt_llm()` that discards structured response data (session_id, metadata, raw_response). Removing it is a prerequisite for centralized MLflow logging — callers need to use `prompt_llm()` directly so the logging context manager has access to full response data.

## LLM Prompt

```
You are implementing step 1 of issue #551 (see pr_info/steps/summary.md for full context).

Task: Remove `ask_llm()` and migrate all callers to use `prompt_llm()["text"]` instead.

1. Update tests FIRST (TDD):
   - In tests/workflow_utils/test_commit_operations.py: change mock target from `ask_llm` to `prompt_llm`, 
     make mock return an LLMResponseDict (dict with "text" key) instead of a plain string
   - In tests/workflows/create_pr/test_*.py: same change — mock `prompt_llm` instead of `ask_llm`,
     return LLMResponseDict
   - In tests/llm/test_interface.py (if exists): remove tests specific to `ask_llm`
   - Run tests to confirm they fail (mocks point to prompt_llm but code still calls ask_llm)

2. Migrate callers:
   - src/mcp_coder/workflows/create_pr/core.py: replace `ask_llm(...)` with `prompt_llm(...)["text"]`
     Update import from `from mcp_coder.llm.interface import ask_llm` to `from mcp_coder.llm.interface import prompt_llm`
   - src/mcp_coder/workflow_utils/commit_operations.py: same replacement

3. Remove ask_llm:
   - src/mcp_coder/llm/interface.py: delete the `ask_llm` function, remove from `__all__`
   - src/mcp_coder/llm/__init__.py: remove `ask_llm` from import and `__all__`
   - src/mcp_coder/__init__.py: remove `ask_llm` from import and `__all__`

4. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `src/mcp_coder/llm/interface.py` — delete `ask_llm()` function
- `src/mcp_coder/llm/__init__.py` — remove `ask_llm` from imports and `__all__`
- `src/mcp_coder/__init__.py` — remove `ask_llm` from imports and `__all__`
- `src/mcp_coder/workflows/create_pr/core.py` — change import and call
- `src/mcp_coder/workflow_utils/commit_operations.py` — change import and call
- `tests/workflow_utils/test_commit_operations.py` — update mocks
- `tests/workflows/create_pr/test_*.py` — update mocks

## WHAT: Changes Per File

### `interface.py`
- **Delete**: entire `ask_llm()` function (~30 lines)
- **Remove**: `"ask_llm"` from `__all__`

### `create_pr/core.py`
- **Change import**: `from mcp_coder.llm.interface import ask_llm` → `from mcp_coder.llm.interface import prompt_llm`
- **Change call**: `ask_llm(full_prompt, provider=provider, ...)` → `prompt_llm(full_prompt, provider=provider, ...)["text"]`

### `commit_operations.py`
- **Change import**: `from ..llm.interface import ask_llm` → `from ..llm.interface import prompt_llm`
- **Change call**: `response = ask_llm(full_prompt, ...)` → `response = prompt_llm(full_prompt, ...)["text"]`

### `__init__.py` files
- Remove `ask_llm` from all import statements and `__all__` lists

## HOW: Integration Points

No new integration points. This is purely removing a thin wrapper and updating call sites.

## DATA: Return Values

`prompt_llm()` returns `LLMResponseDict` (TypedDict with keys: version, timestamp, text, session_id, provider, raw_response). Callers that only need text append `["text"]` to get the same `str` they got from `ask_llm()`.

## Test Updates

Mock `prompt_llm` to return a dict like:
```python
{"text": "mocked response", "session_id": "test-sid", "provider": "claude",
 "version": "1.0", "timestamp": "2024-01-01T00:00:00", "raw_response": {}}
```
instead of mocking `ask_llm` to return `"mocked response"`.
