# Step 2: Add fallback logic in workflow + conditional completion message

> **Context**: See `pr_info/steps/summary.md` for full issue context (#776).
> This step uses the `get_closing_issue_numbers()` method from step 1 to fill in the
> missing issue number after PR creation, and adjusts the final log message.

## WHERE

- **Production**: `src/mcp_coder/workflows/create_pr/core.py`
- **Tests**: `tests/workflows/create_pr/test_workflow.py`

## WHAT

Two changes in `run_create_pr_workflow()`:

### Change A: Fallback after step 4

After PR creation succeeds and before the label update section, add fallback logic:

```python
# Between step 4 (PR created) and step 5 (cleanup) — after pr_number is known:
if update_issue_labels and cached_issue_number is None:
    # Fallback: query closingIssuesReferences from the new PR
    ...
```

### Change B: Conditional completion message

Replace the hardcoded success message at the end:

```python
# Before (line ~370):
logger.log(OUTPUT, "Create PR workflow completed successfully!")

# After:
if update_issue_labels and cached_issue_number is None:
    logger.log(OUTPUT, "Create PR workflow completed with warnings")
else:
    logger.log(OUTPUT, "Create PR workflow completed successfully!")
```

## HOW

- Import `PullRequestManager` — already imported in `core.py`
- The fallback instantiates `PullRequestManager(project_dir)` and calls `get_closing_issue_numbers(pr_number)`
- Place the fallback **after step 4** (PR number available) and **before step 5** (cleanup), so `cached_issue_number` is populated for the label update that runs after step 5

## ALGORITHM

```
1. After PR creation (step 4), check: update_issue_labels AND cached_issue_number is None
2. If so: create PullRequestManager, call get_closing_issue_numbers(pr_number)
3. If len(issues) == 1: set cached_issue_number = issues[0], log info
4. If len(issues) > 1: warn "multiple closing issues", use issues[0]
5. If len(issues) == 0: log debug, cached_issue_number stays None
6. At end: if update_issue_labels and cached_issue_number is None → "completed with warnings"
```

## DATA

- Input: `pr_number` (int) from step 4's `pr_result["number"]`
- Output: `cached_issue_number` updated in-place (Optional[int])
- No new data structures

## TESTS

Add to `tests/workflows/create_pr/test_workflow.py`:

### In `TestRunCreatePrWorkflow`:

1. **`test_workflow_fallback_finds_issue_via_closing_references`**
   - `validate_branch_issue_linkage` returns `None` (no issue from branch name)
   - Mock `PullRequestManager.get_closing_issue_numbers` to return `[92]`
   - Assert `update_workflow_label` IS called with `validated_issue_number=92`
   - Assert final log message is "completed successfully!" (label update succeeded)

2. **`test_workflow_fallback_multiple_closing_issues_uses_first`**
   - `validate_branch_issue_linkage` returns `None`
   - Mock `get_closing_issue_numbers` to return `[92, 55]`
   - Assert `update_workflow_label` called with `validated_issue_number=92`

3. **`test_workflow_fallback_no_closing_issues_skips_labels`**
   - `validate_branch_issue_linkage` returns `None`
   - Mock `get_closing_issue_numbers` to return `[]`
   - Assert `update_workflow_label` NOT called
   - Assert final log contains "completed with warnings"

4. **`test_workflow_completed_with_warnings_when_no_issue_found`**
   - `update_issue_labels=True`, no issue from branch or fallback
   - Assert final log message is "completed with warnings" (not "successfully")

5. **`test_workflow_skips_fallback_when_issue_already_found`**
   - `validate_branch_issue_linkage` returns `123` (found from branch name)
   - Assert `get_closing_issue_numbers` is NOT called (no unnecessary API call)

## LLM PROMPT

```
Implement step 2 of issue #776. See pr_info/steps/summary.md for context and pr_info/steps/step_2.md for details.

In src/mcp_coder/workflows/create_pr/core.py, add:
1. Fallback logic after step 4 that queries closingIssuesReferences via PullRequestManager
2. Conditional completion message ("completed with warnings" vs "completed successfully!")

Write tests FIRST in tests/workflows/create_pr/test_workflow.py, then implement the changes.
Run all code quality checks after implementation.
```
