# Step 1: Add DISABLE_AUTOUPDATER to prepare_llm_environment()

## Summary Reference

See [summary.md](summary.md) for full context (Issue #740).

## WHERE

- **Test file**: `tests/llm/test_env.py` (existing — append 2 tests)
- **Production file**: `src/mcp_coder/llm/env.py` (existing — add 1 line)

## WHAT

No new functions. One line added inside `prepare_llm_environment()`:

```python
env_vars["DISABLE_AUTOUPDATER"] = os.environ.get("DISABLE_AUTOUPDATER", "1")
```

## HOW

- `os.environ.get` is already imported (`os` is used throughout the file)
- The line goes after the existing `env_vars = { ... }` dict literal, before the `logger.debug(...)` call
- No new imports, no signature changes

## ALGORITHM

```
1. (existing) Build env_vars dict with MCP_CODER_* variables
2. Read DISABLE_AUTOUPDATER from os.environ; default to "1" if absent
3. Add it to env_vars
4. (existing) Log and return env_vars
```

## DATA

Return value of `prepare_llm_environment()` gains one additional key:

```python
{
    "MCP_CODER_PROJECT_DIR": "...",   # existing
    "MCP_CODER_VENV_DIR": "...",      # existing
    "MCP_CODER_VENV_PATH": "...",     # existing
    "DISABLE_AUTOUPDATER": "1",       # NEW — or inherited value
}
```

## TESTS (TDD — write first)

### Test 1: `test_prepare_llm_environment_sets_disable_autoupdater`

- **Setup**: `monkeypatch.delenv("DISABLE_AUTOUPDATER", raising=False)`
- **Act**: Call `prepare_llm_environment(project_dir)`
- **Assert**: `result["DISABLE_AUTOUPDATER"] == "1"`

### Test 2: `test_prepare_llm_environment_preserves_existing_disable_autoupdater`

- **Setup**: `monkeypatch.setenv("DISABLE_AUTOUPDATER", "0")`
- **Act**: Call `prepare_llm_environment(project_dir)`
- **Assert**: `result["DISABLE_AUTOUPDATER"] == "0"`

## COMMIT

One commit: tests + one-line production change.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement Step 1: Add DISABLE_AUTOUPDATER support to prepare_llm_environment().
1. Add the two tests to tests/llm/test_env.py
2. Add the one-line change to src/mcp_coder/llm/env.py
3. Run all code quality checks (pylint, mypy, pytest)
4. Fix any issues until all checks pass
```
