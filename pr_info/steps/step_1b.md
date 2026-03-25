# Step 1b: Remove `ask_llm()` and Migrate Production Callers

## Context

See `pr_info/steps/summary.md` for full context. This is step 1b of issue #551.

Step 1a already updated all tests to mock `prompt_llm` instead of `ask_llm`. This step removes `ask_llm()` from production code and migrates its two callers. CI stays green because tests no longer reference `ask_llm`.

## LLM Prompt

```
You are implementing step 1b of issue #551 (see pr_info/steps/summary.md for full context).
Step 1a already updated all tests to use prompt_llm mocks. Now remove ask_llm from
production code and migrate its callers.

Task: Remove ask_llm() and migrate callers to prompt_llm()["text"].

1. Migrate callers:
   - src/mcp_coder/workflows/create_pr/core.py: replace `ask_llm(...)` with `prompt_llm(...)[\"text\"]`
     Update import from `ask_llm` to `prompt_llm`
   - src/mcp_coder/workflow_utils/commit_operations.py: same replacement

2. Remove ask_llm:
   - src/mcp_coder/llm/interface.py: delete the `ask_llm` function, remove from `__all__`
   - src/mcp_coder/llm/__init__.py: remove `ask_llm` from import and `__all__`
   - src/mcp_coder/__init__.py: remove `ask_llm` from import, `__all__`, and update
     the module docstring that references `ask_llm`

3. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `src/mcp_coder/llm/interface.py` — delete `ask_llm()` function
- `src/mcp_coder/llm/__init__.py` — remove `ask_llm` from imports and `__all__`
- `src/mcp_coder/__init__.py` — remove `ask_llm` from imports, `__all__`, and module docstring
- `src/mcp_coder/workflows/create_pr/core.py` — change import and call
- `src/mcp_coder/workflow_utils/commit_operations.py` — change import and call

## WHAT: Changes Per File

### `interface.py`
- **Delete**: entire `ask_llm()` function (~30 lines)
- **Remove**: `"ask_llm"` from `__all__`

### `create_pr/core.py`
- **Change import**: `from mcp_coder.llm.interface import ask_llm` → `from mcp_coder.llm.interface import prompt_llm`
- **Change call**: `ask_llm(full_prompt, provider=provider, ...)` → `prompt_llm(full_prompt, provider=provider, ...)[\"text\"]`

### `commit_operations.py`
- **Change import**: `from ..llm.interface import ask_llm` → `from ..llm.interface import prompt_llm`
- **Change call**: `response = ask_llm(full_prompt, ...)` → `response = prompt_llm(full_prompt, ...)[\"text\"]`

### `__init__.py` files
- Remove `ask_llm` from all import statements and `__all__` lists
- `src/mcp_coder/__init__.py`: update module docstring that references `ask_llm`

## HOW: Integration Points

No new integration points. This is purely removing a thin wrapper and updating call sites.

## DATA: Return Values

`prompt_llm()` returns `LLMResponseDict` (TypedDict with keys: version, timestamp, text, session_id, provider, raw_response). Callers that only need text append `["text"]` to get the same `str` they got from `ask_llm()`.
