# Step 12 — `prompt_llm` / `prompt_llm_stream` honour their `provider=` argument

`verify --llm-method langchain` with `MCP_CODER_LLM_PROVIDER=claude` exported
prints `Active provider: langchain (from cli argument)` and then sends the test
prompt to **claude**: `interface.py:154` and `:337` re-apply the env override
over the argument they were handed. Same class as every other bug in this issue —
an environment variable silently overriding explicit configuration.

Must land **before** step 13 so the test prompt provably reaches the provider
`verify` reported on.

## WHERE

- `src/mcp_coder/llm/interface.py`
- `tests/llm/test_interface.py` — inverts two existing tests (`:1046`, `:1385`)

## WHAT

```python
def prompt_llm(question: str, provider: str | None = None, ...) -> LLMResponseDict: ...
def prompt_llm_stream(question: str, provider: str | None = None, ...) -> Iterator[StreamEvent]: ...
```

## HOW

- Replace `provider = os.environ.get("MCP_CODER_LLM_PROVIDER") or provider` with
  a sentinel-aware resolution in both functions:
  ```python
  provider = provider or os.environ.get("MCP_CODER_LLM_PROVIDER") or "claude"
  ```
  The default changes from `"claude"` to `None`, which is what makes "explicit"
  distinguishable from "defaulted".
- **The config tier stays at the CLI layer.** `cli/utils.resolve_llm_method`
  already implements CLI > env > `[llm] default_provider` > `claude`, and every
  entry point calls it before `prompt_llm`. End-to-end precedence is therefore
  explicit > env > config with no duplicated resolution and no `llm → cli` import
  (which would break the layer contracts).
- No call-site changes needed: every in-repo caller already passes `provider=`
  explicitly. Verify this with a grep before finishing.
- Keep the existing unsupported-provider `ValueError` after resolution, so it can
  never see `None`.
- Update both docstrings: `provider` is now "explicit provider; when omitted,
  `MCP_CODER_LLM_PROVIDER` then `claude`".

## ALGORITHM

```
prompt_llm(question, provider=None, ...):
    validate question / timeout
    provider = provider or os.environ.get("MCP_CODER_LLM_PROVIDER") or "claude"
    if provider not in SUPPORTED_PROVIDERS: raise ValueError(...)
    ... unchanged ...
```

## DATA

| call | env | result |
|---|---|---|
| `prompt_llm(q, provider="langchain")` | `claude` | **langchain** (was claude) |
| `prompt_llm(q)` | `langchain` | langchain (unchanged) |
| `prompt_llm(q)` | unset | claude (unchanged) |

## TDD

Invert and rename the two existing tests:

1. `test_interface.py:1043` — explicit `provider="claude"` with
   `MCP_CODER_LLM_PROVIDER=langchain` now reaches **claude**.
2. `test_interface.py:1382` — same for `prompt_llm_stream`.
3. New: omitted `provider` + env set → env wins (env support preserved).
4. New: omitted `provider` + env unset → claude.
5. New: `provider="unsupported_xyz"` still raises `ValueError`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_12.md`.
> Implement step 12: change `provider` to `str | None = None` in both
> `prompt_llm` and `prompt_llm_stream` (`llm/interface.py`) and resolve
> `provider or MCP_CODER_LLM_PROVIDER or "claude"`, so an explicitly passed
> provider always wins over the environment variable. Do **not** add config
> lookup here — `cli/utils.resolve_llm_method` already owns that tier. Update the
> docstrings. Invert the two existing tests that assert the opposite
> (`tests/llm/test_interface.py` around lines 1046 and 1385) and add coverage for
> the omitted-argument paths. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
