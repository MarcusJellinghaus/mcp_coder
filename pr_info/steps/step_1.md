# Step 1: Add `prepare_env` helper + `env_remove` on `CommandOptions`

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #618).
> This step creates the core building block that all subsequent steps depend on.

## LLM Prompt

```
Implement Step 1 of Issue #618 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).

Add the `prepare_env` helper function and `env_remove` field to `CommandOptions` in subprocess_runner.py.
Write tests first (TDD), then implement. Run all three code quality checks after changes.
```

## WHERE

- `tests/utils/test_subprocess_runner.py` — add tests
- `src/mcp_coder/utils/subprocess_runner.py` — add `prepare_env`, modify `CommandOptions`

## WHAT

### 1. Add `env_remove` field to `CommandOptions`

```python
@dataclass
class CommandOptions:
    # ... existing fields ...
    env_remove: list[str] | None = None
```

### 2. Add `prepare_env` helper (not in `__all__`)

```python
def prepare_env(
    command: list[str] | str,
    env: dict[str, str] | None,
    env_remove: list[str] | None,
) -> dict[str, str]:
```

## ALGORITHM (pseudocode)

```
def prepare_env(command, env, env_remove):
    if isinstance(command, list) and is_python_command(command):
        result = get_python_isolation_env()       # os.environ.copy() + python isolation
    else:
        result = get_utf8_env()                   # os.environ.copy() + utf8 settings
    if env:
        result.update(env)                        # merge caller env on top
    for key in (env_remove or []):
        result.pop(key, None)                     # remove specified keys
    return result
```

## DATA

- **Input**: `command` (list or str), `env` (optional dict), `env_remove` (optional list of key names)
- **Output**: Complete env dict ready for `subprocess.Popen`
- String commands → always treated as non-Python (shell=True implies unknown executable)

## HOW

- `prepare_env` is placed in `subprocess_runner.py` near the existing `get_python_isolation_env` / `get_utf8_env` functions
- Named `prepare_env` (no underscore) because it's imported by `subprocess_streaming.py`. Not added to `__all__` — internal helper shared between subprocess modules.
- `env_remove` field on `CommandOptions` defaults to `None` — fully backward compatible

Note: `execute_command()` does not gain an `env_remove` parameter — no current callers need it (YAGNI). Callers needing `env_remove` should use `execute_subprocess` directly.

## TESTS (write first)

Add a new `TestPrepareEnv` class in `test_subprocess_runner.py`:

1. **`test_prepare_env_python_command_uses_isolation_env`** — verify Python command gets `PYTHONUNBUFFERED=1` etc.
2. **`test_prepare_env_non_python_command_uses_utf8_env`** — verify non-Python command gets `PYTHONIOENCODING=utf-8`
3. **`test_prepare_env_string_command_treated_as_non_python`** — verify string command uses utf8 env (not isolation)
4. **`test_prepare_env_merges_caller_env`** — verify `env={"MY_VAR": "hello"}` appears in result
5. **`test_prepare_env_caller_env_overrides_base`** — verify caller env takes precedence over base
6. **`test_prepare_env_env_remove_removes_keys`** — verify `env_remove=["FOO"]` removes FOO from result
7. **`test_prepare_env_env_remove_ignores_missing_keys`** — verify no error if key not present
8. **`test_prepare_env_none_env_still_inherits_parent`** — verify `env=None` still gets full parent env (the core bug scenario)

Add a test for the new `CommandOptions` field:

9. **`test_command_options_env_remove_default_none`** — verify default is None

### Integration test (new class `TestPrepareEnvIntegration`)

10. **`test_prepare_env_integration_real_env`** — Integration test calling `prepare_env` directly with real `os.environ`. Verify:
   - Result contains `PATH` (inherited from parent)
   - Caller-provided env vars are present
   - `env_remove` keys are absent
   This validates the core bug scenario (env inheritance) without needing to capture launch_process output.

Use `@pytest.mark.parametrize` where appropriate — e.g., combine `test_prepare_env_env_remove_removes_keys` and `test_prepare_env_env_remove_ignores_missing_keys` into one parameterized test.

## COMMIT MESSAGE

```
feat: add prepare_env helper and env_remove to CommandOptions (#618)
```
