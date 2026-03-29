# Step 3: Fix `launch_process()` env inheritance

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #618).
> This step fixes the main bug: `launch_process()` losing parent env vars.

## LLM Prompt

```
Implement Step 3 of Issue #618 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).

Fix launch_process() to use _prepare_env for proper env inheritance. Add env_remove parameter.
Write tests first (TDD), including an integration test with a real subprocess. Run all three code quality checks.
```

## WHERE

- `tests/utils/test_subprocess_runner.py` — add unit + integration tests
- `src/mcp_coder/utils/subprocess_runner.py` — fix `launch_process`

## WHAT

### Fix `launch_process()` signature and implementation

**Before**:
```python
def launch_process(
    command: list[str] | str,
    cwd: str | Path | None = None,
    shell: bool = False,
    env: dict[str, str] | None = None,
) -> int:
    cwd_str = str(cwd) if cwd else None
    process = subprocess.Popen(
        command, cwd=cwd_str, shell=shell, env=env,  # BUG: passes env directly
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return process.pid
```

**After**:
```python
def launch_process(
    command: list[str] | str,
    cwd: str | Path | None = None,
    shell: bool = False,
    env: dict[str, str] | None = None,
    env_remove: list[str] | None = None,
) -> int:
    cwd_str = str(cwd) if cwd else None
    prepared_env = _prepare_env(command, env, env_remove)
    process = subprocess.Popen(
        command, cwd=cwd_str, shell=shell, env=prepared_env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return process.pid
```

## ALGORITHM

```
def launch_process(command, cwd, shell, env, env_remove):
    cwd_str = str(cwd) if cwd else None
    prepared_env = _prepare_env(command, env, env_remove)    # always inherit parent env
    process = Popen(command, cwd=cwd_str, shell=shell, env=prepared_env, ...)
    return process.pid
```

## DATA

- **Input**: same as before + new `env_remove: list[str] | None = None`
- **Output**: PID (int) — unchanged
- **Key change**: `env=None` now produces full parent env (via `_prepare_env`) instead of passing `None` to Popen

## TESTS

### Unit tests (in `TestLaunchProcess` class)

1. **`test_launch_process_inherits_parent_env`** — mock Popen, pass `env=None`, verify the env dict passed to Popen contains parent env vars (e.g., `PATH`)
2. **`test_launch_process_merges_custom_env`** — pass `env={"CUSTOM": "val"}`, verify Popen gets both `CUSTOM` and parent vars
3. **`test_launch_process_env_remove`** — pass `env_remove=["FOO"]` with `env={"FOO": "bar"}`, verify FOO not in Popen's env

### Integration test (new class `TestLaunchProcessIntegration`)

4. **`test_launch_process_real_subprocess_inherits_env`** — This is the **key bug verification test**.
   Run a real subprocess: `python -c "import os; print(os.environ.get('PATH', 'MISSING'))"` 
   with `env={"CUSTOM_TEST_VAR": "hello"}`.
   Verify both `PATH` (inherited) and `CUSTOM_TEST_VAR` (added) are present.
   
   Note: Since `launch_process` discards output (DEVNULL), this test should use `execute_subprocess` 
   or `subprocess.run` directly to verify `_prepare_env` produces correct env. Alternatively, 
   use `_prepare_env` directly in the integration test to verify the env dict, then trust that
   `launch_process` passes it to Popen (already verified by unit test).

## COMMIT MESSAGE

```
fix: launch_process() now inherits parent env vars via _prepare_env (#618)
```
