# Step 2: Update integration test for `run_all_checks` with TERM=dumb

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #792

## LLM Prompt
> Implement step 2 of `pr_info/steps/summary.md`. Update the `TestWarningsLoggedViaRunAllChecks` integration test in `tests/utils/test_tui_preparation.py` — it sets `TERM=dumb` and expects a warning via `run_all_checks`, but now needs `SSH_CONNECTION` set for the warning to fire. Run all code quality checks (pylint, mypy, pytest) and fix any issues before committing.

## WHERE
- `tests/utils/test_tui_preparation.py` — `TestWarningsLoggedViaRunAllChecks` class

## WHAT

### Test: `test_warnings_logged_via_run_all_checks`
Add `monkeypatch.setenv("SSH_CONNECTION", "192.168.1.1 22 192.168.1.2 54321")` so the SSH guard passes and the TERM=dumb warning is produced.

## HOW
- Single line addition in existing test fixture setup.

## ALGORITHM
```
# In test setup, add:
monkeypatch.setenv("SSH_CONNECTION", "192.168.1.1 22 192.168.1.2 54321")
# Rest of test unchanged — TERM=dumb still triggers warning through run_all_checks
```

## DATA
- No change to assertions — test still verifies OUTPUT-level log was called.

## Commit
```
test: add SSH_CONNECTION to run_all_checks integration test (#792)
```
