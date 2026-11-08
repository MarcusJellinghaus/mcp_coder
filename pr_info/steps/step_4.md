# Step 4 — `resolve_target` imports `_create_chat_model` from `._setup`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`).
> Retarget the tests that stub `resolve_target`'s chat-model construction first,
> then change the lazy import in `_config_diagnostics.resolve_target`. No behaviour
> change. Run pylint, pytest, mypy, lint-imports, format, then commit as one commit.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py`
- `tests/llm/providers/langchain/test_langchain_resolve_target.py`
- `tests/llm/providers/langchain/test_langchain_base_url_shape.py` (`_CREATE` constant)

## WHAT

In `resolve_target(config)`:
```python
from ._setup import _create_chat_model  # pylint: disable=cyclic-import
```
replaces `from . import _create_chat_model  # pylint: disable=cyclic-import`.
Keep it **lazy**: `_setup` imports `validate` from `_config_diagnostics` at module level.

## HOW

1. **Tests first.** A stale patch on the package-level `_create_chat_model`
   fails silently once `resolve_target` stops looking it up there. Retarget to
   `mcp_coder.llm.providers.langchain._setup._create_chat_model` **only** the
   patches meant to stub `resolve_target`:
   - `test_langchain_resolve_target.py` (the package-level `_create_chat_model` target, around line 34);
   - `test_langchain_base_url_shape.py`: `_CREATE = f"{_PACKAGE}._create_chat_model"` → `f"{_PACKAGE}._setup._create_chat_model"`.
   Then check every other test that calls `resolve_target` or `verify_langchain`
   (directly or via `execute_verify`) while patching `_create_chat_model`; retarget
   those too. Patches that stub `_ask_text`, `_ask_agent`, streaming etc. stay on
   the package — those call sites are in `__init__`.
2. Change the import in `resolve_target`.
3. Fix the wrong statements about `validate`:
   - module docstring ("Import direction matters" paragraph): the package
     `__init__` imports `dialed_url` (not `validate`); `_setup` imports `validate`
     at module level, so `_setup` may only be imported lazily from here.
   - the inline comment above the import in `resolve_target`: same correction.
4. Run pylint on `_config_diagnostics.py` and `_setup.py`: the line-level
   `cyclic-import` disable must still cover the new direct cycle. If pylint
   reports `cyclic-import` anyway, write one line to `pr_info/.blocked.txt` and stop.

## ALGORITHM

None — import target change.

## DATA

`ResolvedTarget` unchanged.
