# Step 3 — Warn on the retired `MCP_CODER_LLM_LANGCHAIN_ENDPOINT`

Unknown-key detection scans *config sections*, not the environment, so a still
exported `MCP_CODER_LLM_LANGCHAIN_ENDPOINT` produces no signal at all after step
1. `verify` checks for it explicitly (Decision 17), **unconditionally** — outside
both provider gates (Decision 20).

## WHERE

- `src/mcp_coder/cli/commands/verify.py`
- `tests/cli/commands/test_verify_orchestration.py` (or the closest existing
  verify-orchestration test module)

## WHAT

```python
def _print_retired_env_var_warning(symbols: dict[str, str]) -> None:
    """Warn (exit-neutral) when a retired MCP_CODER_* env var is still exported."""
```

## HOW

- Module-level table so future retirements have a home:
  ```python
  _RETIRED_ENV_VARS: dict[str, str] = {
      "MCP_CODER_LLM_LANGCHAIN_ENDPOINT": "MCP_CODER_LLM_LANGCHAIN_BASE_URL",
  }
  ```
- Call it in `execute_verify` right after the CONFIG section is printed —
  **not** inside `_print_langchain_readiness_warning`, whose call site
  (`verify.py:430`) is the else-branch of the langchain gate and would skip
  langchain users.
- Prints only; builds no result dict, so it can never affect the exit code.
- Same commit: fix `_print_langchain_readiness_warning`'s docstring
  (`verify.py:256`), which claims "Runs regardless of active provider" while its
  only call site is provider-gated. State the truth: it runs for non-langchain
  providers.

## ALGORITHM

```
for old, new in _RETIRED_ENV_VARS.items():
    if os.environ.get(old):
        print(row(old, WARN, f"retired env var is set and ignored — use {new}"))
```

## DATA

Output row (exit-neutral):

```
  MCP_CODER_LLM_LANGCHAIN_ENDPOINT  [WARN] retired env var is set and ignored — use MCP_CODER_LLM_LANGCHAIN_BASE_URL
```

The label is longer than `_LABEL_WIDTH` (22); pass
`label_width=len("MCP_CODER_LLM_LANGCHAIN_ENDPOINT")` to `_format_row` so the
value column stays aligned.

## TDD

1. Env var set + `active_provider == "langchain"` → warning appears in captured
   stdout **and** the exit code is unchanged.
2. Env var set + `active_provider == "claude"` → warning still appears.
3. Env var unset → nothing printed.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`.
> Implement step 3: add `_print_retired_env_var_warning()` to
> `cli/commands/verify.py`, driven by a `_RETIRED_ENV_VARS` table, and call it
> unconditionally (outside both provider gates) so it fires whatever the active
> provider is. It must print only and never influence the exit code. In the same
> commit, correct the misleading docstring of
> `_print_langchain_readiness_warning`. Write tests first (TDD), covering both
> the langchain-active and claude-active cases.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
