# Step 1: Reorder workflow steps and update tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement step 1: Reorder the steps in `run_create_pr_workflow()` in `core.py` so cleanup happens before push and PR creation. Update all affected tests in `test_workflow.py` and `test_failure_handling.py`. Run all three quality checks (pylint, pytest, mypy) and fix any issues.

## WHERE

- `src/mcp_coder/workflows/create_pr/core.py` — the `run_create_pr_workflow()` function
- `tests/workflows/create_pr/test_workflow.py` — workflow orchestration tests
- `tests/workflows/create_pr/test_failure_handling.py` — failure handling tests

## WHAT

No new functions. Changes are within `run_create_pr_workflow()` only.

### Production code changes in `core.py`

Reorder the try-block in `run_create_pr_workflow()` to:

```
Step 1/5: Check prerequisites          (unchanged)
Step 2/5: Generate PR summary           (unchanged)
Step 3/5: Clean up repository           (moved from old step 5)
Step 4/5: Push commits                  (moved from old step 3, single push)
Step 5/5: Create pull request           (moved from old step 4, absorbs closing-issues fallback + label update)
```

### Specific changes

1. **Step 3 — Cleanup** (move the cleanup block from after PR creation to after summary generation):
   - Call `cleanup_repository(project_dir)` — on failure, call `_handle_create_pr_failure(stage="cleanup", ...)` **without** `pr_url`, `pr_number`, or `is_cleanup_failure` kwargs → return 1
   - Check `is_working_directory_clean()` — if dirty, call `commit_all_changes("chore: clean up build artifacts", project_dir)`
   - On commit failure (ignoring "No staged files"), call `_handle_create_pr_failure(stage="cleanup", ...)` **without** `pr_url`, `pr_number`, or `is_cleanup_failure` → return 1
   - No push here — that's step 4

2. **Step 4 — Push** (single push, no changes to logic):
   - Call `git_push(project_dir)` — on failure, `_handle_create_pr_failure(stage="push", ...)` → return 1
   - Log success

3. **Step 5 — Create PR + fallback + labels**:
   - Call `create_pull_request()` — on failure, `_handle_create_pr_failure(stage="pr_creation", ...)` → return 1
   - Log PR details
   - Closing-issues-references fallback (unchanged logic, stays here because it needs the PR)
   - Label update (unchanged logic, stays here)
   - Final success/warnings message

4. **Update all `Step N/5` log messages** to match new numbering

5. **Change cleanup commit message**: `"Clean up pr_info temporary folders"` → `"chore: clean up build artifacts"`

6. **Remove the second `git_push()` call** that was in the old cleanup step (no longer needed)

## ALGORITHM (new step order pseudocode)

```
# After steps 1-2 (prerequisites + summary generation):
# Step 3: Cleanup
if not cleanup_repository(project_dir): abort("cleanup")
if not is_working_directory_clean(project_dir):
    result = commit_all_changes("chore: clean up build artifacts", project_dir)
    if not result["success"] and "No staged files" not in error: abort("cleanup")

# Step 4: Push (single push covers feature + cleanup commits)
if not git_push(project_dir)["success"]: abort("push")

# Step 5: Create PR, then closing-issues fallback, then label update
pr_result = create_pull_request(project_dir, title, body)
if pr_result is None: abort("pr_creation")
# ... closing-issues fallback (unchanged) ...
# ... label update (unchanged) ...
```

## DATA

No changes to return values or data structures. `run_create_pr_workflow()` still returns `int` (0 or 1).

## Test changes in `test_workflow.py`

- **`test_workflow_complete_success`**: Assert `mock_push.call_count == 1` (was 2). Cleanup is called before push and PR creation.
- **`test_workflow_pr_creation_fails`**: Now needs `mock_cleanup`, `mock_clean`, and optionally `mock_commit` mocks since cleanup happens before PR creation. Add mocks for `cleanup_repository` returning True and `is_working_directory_clean` returning True.
- **`test_workflow_execution_dir_passed_to_generate_summary`**: Assert `mock_push.call_count == 1` (was implicitly 1, just verify).
- **Tests with `update_issue_labels`**: Add cleanup/clean mocks where missing since cleanup now runs before PR creation.

## Test changes in `test_failure_handling.py`

- **`test_push_failure_is_fatal`**: Add `mock_cleanup` and `mock_clean` mocks (cleanup now runs before push). Mock cleanup returning True and clean returning True.
- **`test_pr_creation_failure`**: Add `mock_cleanup` and `mock_clean` mocks.
- **`test_cleanup_failure_includes_pr_link`**: Rename to reflect cleanup now happens before PR. Remove assertions on `pr_url`, `pr_number`, `is_cleanup_failure` — these no longer apply. Remove `mock_create_pr` and `mock_push` mocks (cleanup is step 3, before push/PR). The failure handler call should NOT have `pr_url`/`pr_number`/`is_cleanup_failure` kwargs.
- **`test_cleanup_commit_failure`**: Remove `mock_create_pr` and `mock_push` mocks. Remove assertions on `is_cleanup_failure`. Remove `pr_url`/`pr_number` from expected kwargs.
- **`test_cleanup_push_failure`**: **Delete this test entirely** — there is no separate cleanup push anymore. The single push is in step 4 and is already covered by `test_push_failure_is_fatal`.

## Commit

```
feat(create-pr): reorder cleanup before push and PR creation (#759)
```
