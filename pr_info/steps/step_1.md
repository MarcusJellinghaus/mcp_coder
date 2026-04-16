# Step 1 — Status Symbols + Arrow Rename

## Goal

Drop platform-branching in `_get_status_symbols()`. Replace with an ASCII-only constant on all platforms, rename `[NO]`→`[ERR]` and `[!!]`→`[WARN]`, and replace Unicode `→` with ASCII `->`. Update all tests that assert the old labels.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1 as a single commit: ASCII-only `STATUS_SYMBOLS` constant in `verify.py`, delete `_get_status_symbols` from `cli/utils.py`, delete `tests/cli/test_utils_status_symbols.py`, replace Unicode arrow `→` (`\u2192`) with `->`, and update all test assertions across the 6 verify test files from `[NO]`/`[!!]`/`→` to `[ERR]`/`[WARN]`/`->`. Run pylint, pytest, mypy — all must pass.

## WHERE

- **Modify:** `src/mcp_coder/cli/commands/verify.py`, `src/mcp_coder/cli/utils.py`
- **Delete:** `tests/cli/test_utils_status_symbols.py`
- **Update tests:** `tests/cli/commands/test_verify.py`, `test_verify_command.py`, `test_verify_exit_codes.py`, `test_verify_format_section.py`, `test_verify_integration.py`, `test_verify_orchestration.py`

## WHAT

```python
# verify.py (top of module, after imports)
STATUS_SYMBOLS: dict[str, str] = {
    "success": "[OK]",
    "failure": "[ERR]",
    "warning": "[WARN]",
}
```

In `execute_verify`, replace `symbols = _get_status_symbols()` with `symbols = STATUS_SYMBOLS`.

In `_format_section`, replace `"\u2192"` with `"->"`.

## HOW

- Remove `_get_status_symbols` import from `verify.py`.
- Remove `_get_status_symbols` from `__all__` in `cli/utils.py`.
- Delete `_get_status_symbols` function body in `cli/utils.py`.
- Delete `tests/cli/test_utils_status_symbols.py`.
- Global string replacements in the 6 verify test files:
  - `"[NO]"` → `"[ERR]"` (in assertion strings and helper `_symbols()` dicts)
  - `"[!!]"` → `"[WARN]"`
  - `"\u2192"` → `"->"`

## ALGORITHM

N/A — rename + constant extraction. No new logic.

## DATA

- `STATUS_SYMBOLS`: `dict[str, str]` with keys `"success"`, `"failure"`, `"warning"`.

## Verification

- `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`
- `mcp__tools-py__run_pylint_check()`
- `mcp__tools-py__run_mypy_check()`
