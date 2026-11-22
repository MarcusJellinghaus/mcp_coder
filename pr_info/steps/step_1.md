# Step 1 — Shared `LLMAuthError` type

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit markers),
> mypy and lint-imports; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/llm/types.py`
- `src/mcp_coder/llm/interface.py`
- `src/mcp_coder/llm/providers/langchain/_exceptions.py`
- `.importlinter`, contract `langchain_model_layer`
- Tests: `tests/llm/test_types.py` if it exists and stays under 750 lines; otherwise create
  `tests/llm/test_llm_auth_error.py`.

## WHAT

```python
# llm/types.py  (stdlib only — no mcp_coder imports)
class LLMAuthError(Exception):
    """Authentication failure from an LLM provider (Claude CLI login, API key, ...)."""
```

- Add `"LLMAuthError"` to `types.__all__`.
- `interface.py`: import it from `.types` alongside `SUPPORTED_PROVIDERS, LLMResponseDict, StreamEvent`,
  and add `"LLMAuthError"` to `interface.__all__`.
- `_exceptions.py`: delete the local `class LLMAuthError` and put this in its place,
  after `from typing import NoReturn`:
  ```python
  from mcp_coder.llm.types import LLMAuthError as LLMAuthError
  ```
  The absolute path and the explicit alias are required: mypy `no_implicit_reexport` keeps
  `_provider_checks.py` and the tests importing it from `_exceptions`.
- `.importlinter` `langchain_model_layer` → `ignore_imports`: add
  `mcp_coder.llm.providers.langchain._exceptions -> mcp_coder.llm.types` next to the `_usage` line.

## HOW

- No caller changes. `_provider_checks.py`, `raise_auth_error` and the langchain tests keep
  importing `LLMAuthError` from `_exceptions`.

## DATA

- No new data. `LLMAuthError` subclasses only `Exception`.

## Tests (first)

- `LLMAuthError` from `mcp_coder.llm.types`, `mcp_coder.llm.interface` and
  `mcp_coder.llm.providers.langchain._exceptions` is the same object (`is`).
- `issubclass(LLMAuthError, Exception)` holds, and it is not a subclass of `OSError`,
  `TimeoutError` or `CalledProcessError`.
- The existing langchain tests (`test_langchain_exceptions.py` and others) pass unchanged.
- lint-imports passes.
