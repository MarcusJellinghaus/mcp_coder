# Step 2 — Move `_load_langchain_config` to `_config_source.py`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Retarget the tests first (they fail), then move `_load_langchain_config` out of
> `_setup.py` into a new `_config_source.py`. No behaviour change. Run pylint,
> pytest, mypy, lint-imports, format, then commit as one commit.

## WHERE

- New: `src/mcp_coder/llm/providers/langchain/_config_source.py`
- Modified: `_setup.py`, `__init__.py`, `verification.py` (same package)
- Tests: `tests/llm/providers/langchain/test_langchain_provider.py` (class removed),
  new `tests/llm/providers/langchain/test_langchain_config_source.py` (class moved in)

## WHAT

```python
# _config_source.py
"""Read the LangChain config from mcp-coder's config.toml (outside the model layer)."""
logger = logging.getLogger(__name__)

def _load_langchain_config() -> dict[str, str | None]: ...  # moved verbatim
```

Body, docstring and warning text are moved unchanged (including the
`` `mcp-coder verify` `` warning — it leaves the model layer with this function).

## HOW

1. **Tests first:** move the whole `TestLoadLangchainConfig` class from
   `test_langchain_provider.py` into a new
   `tests/llm/providers/langchain/test_langchain_config_source.py` (with the
   imports it needs). In the moved class change every
   `"mcp_coder.llm.providers.langchain._setup.get_config_values"` to
   `"mcp_coder.llm.providers.langchain._config_source.get_config_values"` and
   import `_load_langchain_config` from
   `mcp_coder.llm.providers.langchain._config_source`.
   Search all tests for `_setup.get_config_values` and `_setup._load_langchain_config`;
   retarget any other hit the same way. Remove imports left unused in
   `test_langchain_provider.py`.
2. Create `_config_source.py`; imports: `logging`, `typing.Any`,
   `from mcp_coder.utils.user_config import get_config_values`.
3. `_setup.py`: delete `_load_langchain_config` and the
   `get_config_values` import. Keep `logging`/`uuid` for now (step 3 removes them).
4. `__init__.py`: replace
   `from ._setup import _load_langchain_config as _load_langchain_config` with
   `from ._config_source import _load_langchain_config as _load_langchain_config`
   so every package-level patch (`mcp_coder.llm.providers.langchain._load_langchain_config`)
   keeps working. Update the re-export comment above it to name the source modules.
5. `verification.py`: replace `from . import _load_langchain_config` with
   `from ._config_source import _load_langchain_config` (module-level name kept,
   so `verification._load_langchain_config` patches keep working).
6. `verify_sections.py` keeps `from ...llm.providers.langchain import _load_langchain_config`.

## ALGORITHM

None — pure move.

## DATA

Unchanged: dict with keys `default_provider, backend, model, api_key, base_url,
api_version`, every value `str | None`.
