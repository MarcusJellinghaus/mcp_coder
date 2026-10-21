# Step 3 — Enable ruff `F` and clean `src`

**Commit:** `build(ruff): enable F (pyflakes)`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly.
> Add `"F"` to the ruff `select` list. Delete the 4 dead `src` imports. Rewrite the 5
> optional-dependency checks as `import x` + `del x` without `noqa`. Update the two
> `pyproject.toml` comments. Do not use `find_spec` or `importlib.import_module`. Run all
> checks listed in the summary, then make one commit.

## WHERE

- `pyproject.toml`
- `src/mcp_coder/cli/commands/coordinator/core.py`
- `src/mcp_coder/workflows/create_pr/helpers.py`
- `src/mcp_coder/llm/storage/session_finder.py`
- `src/mcp_coder/llm/providers/langchain/__init__.py`
- `src/mcp_coder/llm/mlflow_logger.py`
- `src/mcp_coder/llm/providers/langchain/agent.py`
- `src/mcp_coder/llm/providers/langchain/_exceptions.py`
- `src/mcp_coder/llm/providers/langchain/_preflight.py`

## WHAT / HOW

**`pyproject.toml`**
- `[tool.ruff.lint] select`: add `"F",`, for example next to `"E"`.
- Line 328: replace `# Only enable docstring rules for now` with a comment that matches
  reality, for example `# Rule selection — see the per-group comments below`.
- Line 208: replace the `W0611` comment with
  `"W0611",   # unused-import — owned by ruff F401 (pylint flags the X-as-X re-export convention)`.
  `W0611` stays disabled.

**Dead imports (delete):**
- `coordinator/core.py:10`: `Optional`
- `create_pr/helpers.py:10`: `Optional`
- `storage/session_finder.py:12`: `Path`
- `langchain/__init__.py:28`: `from ._exceptions import LLMMCPLaunchError`

If removing a name empties its `from … import` line, delete the whole line.

**Optional-dependency checks: `import x` + `del x`.** Remove `# noqa: F401` and
`unused-import` from each line. Keep every other pragma, except the mlflow
`# type: ignore[...]` (see below).

| File:line | New code |
|---|---|
| `mlflow_logger.py:48` | `import mlflow  # pylint: disable=import-error` then `del mlflow` (drop the `# type: ignore[...]` too — see below) |
| `agent.py:49` | `import langchain_mcp_adapters` then `del langchain_mcp_adapters` |
| `agent.py:53` | `import langgraph` then `del langgraph` |
| `_exceptions.py:237` | `import truststore  # pylint: disable=import-outside-toplevel` then `del truststore` (before `return True`) |
| `_preflight.py:28` | `import ollama  # pylint: disable=import-outside-toplevel,import-error` then `del ollama` |

If pylint reports `import-outside-toplevel` at an `agent.py` site after the change, add
that disable on the import line. Do not re-add `unused-import`.

`mlflow_logger.py:48`: today the `# type: ignore[...]` follows `# noqa: F401`, so mypy
ignores it. With the `noqa` gone it would become the first comment and mypy would act on
it. `pyproject.toml` already covers mlflow (`ignore_missing_imports`,
`disable_error_code = ["import-untyped"]`), so strict mode would report it as an unused
ignore. Drop it, matching the other `import mlflow` sites. Run `run_mypy_check` after
the change and confirm it passes.

## ALGORITHM (each optional-dependency site)

```
try:
    import x          # real import: honours __import__ patches and sys.modules mocks
    del x             # binding consumed -> no F401, no noqa
    <unchanged success path>
except ImportError:
    <unchanged failure path>
```

## DATA

Return values do not change:
- `is_mlflow_available() -> bool`
- `_truststore_available() -> bool`

`agent.py` still raises `ImportError` listing missing packages, and `_ollama_preflight`
still raises `ImportError` with install instructions.

## Precondition

After adding `"F"`, `run_ruff_check(select=["F"])` on `src` and `tests` should show only
the 4 dead `src` imports listed above. If it reports any other `F` finding, write one line
to `pr_info/.blocked.txt` and stop.

## Tests (TDD)

The existing tests already specify the behaviour of every changed function:
- `tests/llm/test_mlflow_logger.py` (patches `builtins.__import__`)
- `tests/llm/providers/langchain/test_langchain_agent.py`
- the langchain `_exceptions` / `_preflight` tests

Run them first, so they are green before the change, and again after. No new tests.

## Acceptance (end of PR)

- `run_ruff_check()` with project config is clean. `F` is in `select`, with no `F`
  per-file-ignores.
- `search_files(pattern="noqa: F(401|811)")` finds nothing in `src` or `tests`.
- `.importlinter` has no `tests.utils.conftest` entries (done in step 1).
- Every name in the `.claude/CLAUDE.md` shim table is in that shim's `__all__`. Read the 3
  shims to verify; no change is expected.
- pylint, mypy and `lint-imports` pass. pytest passes for the unit run and for
  `git_integration`.
