# Step 1: Add stdout confirmation on success + update tests

## Context

See `pr_info/steps/summary.md` for full context.  
Issue #635: `execute_set_status()` succeeds silently — LLM callers see `(No output)`.

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. In
> `src/mcp_coder/cli/commands/set_status.py`, add a `print()` call on the success
> path of `execute_set_status()`. Then update the 4 success-path tests in
> `tests/cli/commands/test_set_status.py` to assert the expected stdout message.
> Run all code quality checks (pylint, mypy, pytest) and fix any issues.

## WHERE

- `src/mcp_coder/cli/commands/set_status.py` — production code
- `tests/cli/commands/test_set_status.py` — test code

## WHAT

No new functions. One `print()` line added to existing `execute_set_status()`.

## HOW

In `execute_set_status()`, immediately before the existing `logger.info(...)` line
on the success path, add:

```python
print(f"Updated issue #{issue_number} to {args.status_label}")
```

Keep the existing `logger.info()` unchanged.

## ALGORITHM

```
# In execute_set_status(), after _update_issue_labels succeeds:
1. print success message to stdout
2. log success message via logger.info (already exists)
3. return 0 (already exists)
```

## DATA

**Stdout output on success:**
```
Updated issue #635 to status-05:plan-ready
```

## TEST CHANGES

Add `capsys: pytest.CaptureFixture[str]` fixture and stdout assertion to these 4 tests:

1. `test_execute_success_with_branch_detection` — add `capsys`, assert
   `"Updated issue #123 to status-05:plan-ready"` in `captured.out`
2. `test_execute_success_with_explicit_issue` — same
3. `test_execute_set_status_dirty_directory_with_force_succeeds` — same
4. `test_execute_set_status_clean_directory_succeeds` — same

Each test already sets `issue=123` (or extracts 123 from branch) and uses
`status_label="status-05:plan-ready"`, so the expected message is identical:

```python
captured = capsys.readouterr()
assert "Updated issue #123 to status-05:plan-ready" in captured.out
```

## COMMIT

```
Add stdout success message to gh-tool set-status (#635)
```
