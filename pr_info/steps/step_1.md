# Step 1: Derive `logs_dir` from `env_vars` in `prompt_llm()` (TDD)

## LLM Prompt
> Read `pr_info/steps/summary.md` for context. Implement Step 1: Add tests for `logs_dir` derivation from `env_vars` in `prompt_llm()`, then implement the fix in `interface.py`, then update existing test assertions. Run all quality checks (pylint, mypy, pytest) and fix any issues.

## WHERE
- `tests/llm/test_interface.py` — new tests + update existing assertions
- `src/mcp_coder/llm/interface.py` — production fix (~4 lines)
- `src/mcp_coder/workflows/create_pr/core.py` — pass `env_vars` to `prompt_llm()`

## WHAT

### New tests to add in `tests/llm/test_interface.py`

Add a new test class `TestPromptLLMLogsDirDerivation` with these tests:

```python
def test_logs_dir_derived_from_env_vars_project_dir(self, mock_ask_claude_code_cli):
    """When env_vars has MCP_CODER_PROJECT_DIR, logs_dir is derived and passed."""

def test_logs_dir_none_when_env_vars_missing_project_dir(self, mock_ask_claude_code_cli):
    """When env_vars lacks MCP_CODER_PROJECT_DIR, logs_dir=None."""

def test_logs_dir_none_when_env_vars_is_none(self, mock_ask_claude_code_cli):
    """When env_vars is None, logs_dir=None (backward compat)."""
```

### Update existing test assertions

All existing `mock_ask_claude_code_cli.assert_called_once_with(...)` calls must add `logs_dir=None` (or the derived value) to match the new kwarg being passed.

For tests that pass `env_vars=None` or no `env_vars`: add `logs_dir=None`
For tests that pass `env_vars` with `MCP_CODER_PROJECT_DIR`: add `logs_dir="{project_dir}/logs"`

Tests that pass `env_vars` dicts without `MCP_CODER_PROJECT_DIR` (e.g., `{"VAR1": "value1"}`) also get `logs_dir=None`.

### Fix `generate_pr_summary()` in `create_pr/core.py`

This caller doesn't pass `env_vars` to `prompt_llm()`, so it wouldn't benefit from the `logs_dir` fix. Add:
- Import `prepare_llm_environment` from `mcp_coder.llm.env`
- Before the `prompt_llm()` call (~line 332): `env_vars = prepare_llm_environment(project_dir)`
- Pass `env_vars=env_vars` to `prompt_llm()`

This follows the same pattern as `implement/core.py`.

### Production change in `src/mcp_coder/llm/interface.py`

**Function:** `prompt_llm()` — Claude provider branch (around line 108)

**Signature:** No change to `prompt_llm()` signature

## HOW

In `prompt_llm()`, before the `ask_claude_code_cli()` call in the Claude provider branch:

```python
# Derive logs_dir from env_vars to store logs in mcp-coder's project dir
logs_dir = None
if env_vars and "MCP_CODER_PROJECT_DIR" in env_vars:
    logs_dir = str(Path(env_vars["MCP_CODER_PROJECT_DIR"]) / "logs")
```

Note: `Path` from `pathlib` — check if already imported in `interface.py`; add if needed.

Then pass it:
```python
response = ask_claude_code_cli(
    question,
    session_id=session_id,
    timeout=timeout,
    env_vars=env_vars,
    cwd=execution_dir,
    mcp_config=mcp_config,
    branch_name=branch_name,
    logs_dir=logs_dir,  # NEW
)
```

## ALGORITHM (pseudocode)
```
1. logs_dir = None
2. if env_vars is not None and "MCP_CODER_PROJECT_DIR" in env_vars:
3.     logs_dir = str(Path(env_vars["MCP_CODER_PROJECT_DIR"]) / "logs")
4. pass logs_dir=logs_dir to ask_claude_code_cli()
```

## DATA
- Input: `env_vars` dict (already exists), key `MCP_CODER_PROJECT_DIR` (str path)
- Output: `logs_dir` (str | None) passed to `ask_claude_code_cli()`
- No new return values or data structures

## CHECKLIST
- [ ] Write 3 new tests in `TestPromptLLMLogsDirDerivation`
- [ ] Update all existing `assert_called_once_with` assertions to include `logs_dir=...`
- [ ] Add 4 lines of production code in `interface.py`
- [ ] Update `create_pr/core.py` to import `prepare_llm_environment` and pass `env_vars` to `prompt_llm()`
- [ ] Run pylint — must pass
- [ ] Run mypy — must pass
- [ ] Run pytest (unit tests) — must pass
