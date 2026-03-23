# Step 2: Integrate CONFIG Section into `verify` Command

> **Reference**: See `pr_info/steps/summary.md` for overall context and architecture.

## Goal

Wire `verify_config()` into the verify command: format and print the CONFIG section, update exit code logic, and add integration tests.

## WHERE

- **Implementation**: `src/mcp_coder/cli/commands/verify.py` — modify `execute_verify()` and `_compute_exit_code()`
- **Tests**: `tests/cli/commands/test_verify_exit_codes.py` — add config exit code tests and CONFIG section integration tests

## WHAT

### Modified: `_compute_exit_code()`

```python
def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
    test_prompt_ok: bool = True,
    mcp_result: dict[str, Any] | None = None,
    config_has_error: bool = False,        # ← NEW PARAMETER
) -> int:
```

### Modified: `execute_verify()`

Add CONFIG section as the **first** section (before BASIC VERIFICATION). Inline formatting:

```python
# 0. Config verification (first section)
config_result = verify_config()
lines = ["\n=== CONFIG ==="]
for entry in config_result["entries"]:
    status = entry["status"]
    symbol = {"ok": symbols["success"], "warning": symbols["warning"],
              "error": symbols["failure"]}.get(status, " ")
    lines.append(f"  {entry['label']:<20s} {symbol} {entry['value']}")
print("\n".join(lines))
```

## HOW

- Import `verify_config` from `...utils.user_config`
- Call `verify_config()` before `verify_claude()`
- Pass `config_has_error=config_result["has_error"]` to `_compute_exit_code()`
- The `"info"` status (used for "Expected path" and "Hint" on missing config) maps to `" "` (space) — no symbol, just indented text

## ALGORITHM

### `_compute_exit_code` change:
```
1. if config_has_error: return 1     # ← NEW: first check
2. if not test_prompt_ok: return 1   # existing
3. ... rest unchanged ...
```

### `execute_verify` change:
```
1. config_result = verify_config()
2. print formatted CONFIG section (loop over entries)
3. ... existing code (claude, langchain, mcp, prompt, mlflow) ...
4. pass config_has_error to _compute_exit_code()
```

## DATA

No new data structures. Uses `verify_config()` return from Step 1.

## TESTS (TDD — write first)

Add to `tests/cli/commands/test_verify_exit_codes.py`:

### Exit code tests in `TestComputeExitCode`:

1. **`test_config_error_returns_exit_1`** — `config_has_error=True` → exit 1, regardless of other results
2. **`test_config_no_error_does_not_affect_exit`** — `config_has_error=False` → no change to exit code (still 0 with ok results)

### Integration tests in new `TestConfigSectionInVerify` class:

3. **`test_config_section_displayed_first`** — mock `verify_config()`, verify "CONFIG" appears in output before "BASIC VERIFICATION"
4. **`test_config_invalid_toml_causes_exit_1`** — mock `verify_config()` returning `has_error=True`, verify exit code is 1
5. **`test_config_missing_shows_warning`** — mock `verify_config()` returning warning entries, verify output contains warning symbol and "not found"

These tests mock `verify_config()` (unit-tested in Step 1) to keep them focused on the verify command's formatting and exit code logic.

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 2.

1. Read src/mcp_coder/cli/commands/verify.py and tests/cli/commands/test_verify_exit_codes.py
2. Add exit code tests and TestConfigSectionInVerify tests to test_verify_exit_codes.py as listed in step_2.md
3. Update _compute_exit_code() to accept config_has_error parameter (check it first, before test_prompt_ok)
4. Update execute_verify() to call verify_config() as the first section, format and print CONFIG output, pass config_has_error to _compute_exit_code()
5. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
6. Commit with message: "feat(verify): integrate CONFIG section into verify command (#552)"
```
