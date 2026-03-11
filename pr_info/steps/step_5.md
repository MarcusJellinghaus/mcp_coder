# Step 5: Final validation — all tests pass, type checks clean

> **Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE
- All 4 source files from steps 1-4
- All test files from steps 1-4
- Additional test files that may reference CI types:
  - `tests/cli/commands/test_check_branch_status_auto_fixes.py`
  - `tests/cli/commands/test_check_branch_status_cli_integration.py`
  - `tests/workflows/implement/test_core.py`

## WHAT — Validation tasks

### 1. Run full test suite
```
pytest tests/utils/github_operations/test_ci_results_manager_status.py
pytest tests/checks/test_branch_status.py
pytest tests/cli/commands/test_check_branch_status.py
pytest tests/cli/commands/test_check_branch_status_ci_waiting.py
pytest tests/cli/commands/test_check_branch_status_auto_fixes.py
pytest tests/workflows/implement/test_ci_check.py
pytest tests/workflows/implement/test_core.py
```

### 2. Fix any remaining test fixtures
Search across all test files for patterns:
- `"run": {"id":` → needs `"run_ids"` update
- `.get("id")` on run dicts in test assertions
- Mock `CIStatusData` constructions missing `run_id` on jobs

### 3. Run mypy type check
Verify `JobData` with new `run_id` field doesn't cause type errors in consumers.

### 4. Run pylint
Check for any new issues introduced by the changes.

## HOW
Use `mcp__code-checker__run_all_checks` or individual check tools.

## DATA
No new code in this step — only fixes to make everything green.

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then execute Step 5 from pr_info/steps/step_5.md.

Run the full test suite for all files touched in this PR. Fix any remaining test failures
caused by the run["id"] → run["run_ids"] migration or missing run_id on JobData.
Then run mypy and pylint. All checks must pass.
```
