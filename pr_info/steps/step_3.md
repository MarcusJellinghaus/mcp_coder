# Step 3 — Move `_resolve_session_id` into `__init__`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`).
> Retarget the test patch first, then move `_resolve_session_id` from `_setup.py`
> into the package `__init__.py`. No behaviour change. Run pylint, pytest, mypy,
> lint-imports, format, then commit as one commit.

## WHERE

- `src/mcp_coder/llm/providers/langchain/__init__.py`
- `src/mcp_coder/llm/providers/langchain/_setup.py`
- `tests/llm/providers/langchain/conftest.py`

## WHAT

```python
# __init__.py
def _resolve_session_id(session_id: str | None) -> str: ...  # moved verbatim
```

## HOW

1. **Tests first:** in `tests/llm/providers/langchain/conftest.py` change
   `patch("mcp_coder.llm.providers.langchain._setup.require_langchain_history")`
   to `patch("mcp_coder.llm.providers.langchain.require_langchain_history")`.
   Search all tests for `_setup.require_langchain_history` and
   `_setup._resolve_session_id`; retarget hits to the package.
   Tests importing `_resolve_session_id` from the package
   (`test_langchain_session_guard.py`, `test_langchain_agent_stream_history.py`) stay.
2. `__init__.py`:
   - add `import uuid`;
   - add `require_langchain_history` to the existing
     `from mcp_coder.llm.storage.session_storage import (...)`;
   - delete `from ._setup import _resolve_session_id as _resolve_session_id`;
   - define `_resolve_session_id` (body and docstring unchanged) before `ask_langchain`.
3. `_setup.py`:
   - delete `_resolve_session_id`, `import uuid`, the
     `require_langchain_history` import, `import logging` and `logger`
     (all unused now — confirm with pylint);
   - update the module docstring: it turns a config into a chat model and system
     messages and maps backend exceptions; drop "a session id", and say that
     callers live outside the module (package `__init__`, `_config_diagnostics`).
   - After this step `_setup.py` imports nothing from `mcp_coder` — check with a
     search for `mcp_coder` in its import lines.

## ALGORITHM

Unchanged:
```
if not session_id: return str(uuid.uuid4())
require_langchain_history(session_id)   # raises ValueError for an unknown id
return session_id
```

## DATA

Returns the session id string.
