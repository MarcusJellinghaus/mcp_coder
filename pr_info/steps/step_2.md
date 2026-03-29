# Step 2: Refactor `_run_subprocess` + `stream_subprocess` to use `prepare_env`; update Claude CLI callers

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #618).
> This step wires up the helper from Step 1 and moves CLAUDECODE removal to callers.

## LLM Prompt

```
Implement Step 2 of Issue #618 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

Refactor _run_subprocess and stream_subprocess to use prepare_env. Update Claude CLI callers
to pass env_remove=["CLAUDECODE"]. Write/update tests first (TDD). Run all three code quality checks.
```

## WHERE

- `tests/utils/test_subprocess_runner.py` — update existing env tests
- `src/mcp_coder/utils/subprocess_runner.py` — refactor `_run_subprocess`
- `src/mcp_coder/utils/subprocess_streaming.py` — refactor `stream_subprocess`, import `prepare_env`
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — add `env_remove`
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — add `env_remove`

## WHAT

### 1. Refactor `_run_subprocess` in `subprocess_runner.py`

**Remove** (lines ~181-192):
```python
    # Prepare environment with UTF-8 encoding support
    if is_python_command(command):
        env = get_python_isolation_env()
        if options.env:
            env.update(options.env)
    else:
        env = get_utf8_env()
        if options.env:
            env.update(options.env)

    # Remove CLAUDECODE to allow nested Claude CLI invocations
    if "CLAUDECODE" in env:
        logger.debug("Removing CLAUDECODE env var to allow nested Claude CLI execution")
        env.pop("CLAUDECODE")
```

**Replace with**:
```python
    env = prepare_env(command, options.env, options.env_remove)
```

### 2. Refactor `stream_subprocess` in `subprocess_streaming.py`

**Remove** the inline env setup block (~lines 115-123):
```python
    if is_python_command(command):
        env = get_python_isolation_env()
        if options.env:
            env.update(options.env)
    else:
        env = get_utf8_env()
        if options.env:
            env.update(options.env)

    # Remove CLAUDECODE to allow nested Claude CLI invocations
    env.pop("CLAUDECODE", None)
```

**Replace with**:
```python
    env = prepare_env(command, options.env, options.env_remove)
```

**Update imports** — add `prepare_env` to the import from `subprocess_runner`, remove `get_python_isolation_env`, `get_utf8_env`, `is_python_command` (no longer needed directly).

### 3. Update Claude CLI callers

**`claude_code_cli.py`** (line ~636):
```python
    options = CommandOptions(
        timeout_seconds=timeout,
        input_data=input_data,
        env=env_vars,
        cwd=cwd,
        env_remove=["CLAUDECODE"],  # ← ADD THIS
    )
```

**`claude_code_cli_streaming.py`** (line ~109):
```python
    options = CommandOptions(
        timeout_seconds=timeout,
        input_data=input_data,
        env=env_vars,
        cwd=cwd,
        env_remove=["CLAUDECODE"],  # ← ADD THIS
    )
```

## HOW

- `prepare_env` is imported in `subprocess_streaming.py` from `.subprocess_runner`
- The CLAUDECODE removal is no longer hardcoded anywhere — it's now caller-controlled
- Behavior is identical to before: Claude CLI callers still remove CLAUDECODE, other callers don't

## TESTS

Note: No existing tests verify CLAUDECODE removal behavior, so removing the hardcoded pop is safe. If any such tests are discovered during implementation, update them in this same step.

Update existing `test_stream_subprocess_env_setup` to verify `prepare_env` is being called (env still has `PYTHONUNBUFFERED=1` for Python commands).

Add tests:
1. **`test_run_subprocess_passes_env_remove_to_prepare_env`** — mock `prepare_env`, verify `_run_subprocess` calls it with `options.env_remove`
2. **`test_stream_subprocess_passes_env_remove`** — verify stream_subprocess passes env_remove through

## COMMIT MESSAGE

```
refactor: use prepare_env in all subprocess functions, move CLAUDECODE removal to callers (#618)
```
