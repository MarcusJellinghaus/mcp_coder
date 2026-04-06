# Step 5: Create-pr helpers — update failure handling params

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/workflows/create_pr/helpers.py` — modify `handle_create_pr_failure()`
- `tests/workflows/create_pr/test_failure_handling.py` — update existing tests

## WHAT

### Changes to `handle_create_pr_failure()`

**Rename parameter:** `update_labels: bool` → `update_issue_labels: bool`

**Add parameter:** `post_issue_comments: bool = False`

**Pass both to `handle_workflow_failure()`:**

```python
def handle_create_pr_failure(
    stage: str,
    message: str,
    project_dir: Path,
    update_issue_labels: bool,        # renamed from update_labels
    post_issue_comments: bool = False, # NEW
    elapsed_time: float | None = None,
    issue_number: int | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
) -> None:
```

## HOW
- Update the call to `handle_workflow_failure()` to pass `update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments`
- No changes to `format_failure_comment()` — it's unaffected
- No changes to `parse_pr_summary()` — it's unaffected

## ALGORITHM
No algorithm change — just parameter renaming and pass-through.

## DATA
- **Input:** `update_labels → update_issue_labels`, new `post_issue_comments`
- **Output:** unchanged (void)

## TESTS

Update existing tests in `tests/workflows/create_pr/test_failure_handling.py`:

1. All calls to `handle_create_pr_failure()` that pass `update_labels=...` → rename to `update_issue_labels=...`
2. Add `post_issue_comments=True` where tests verify comment posting behavior
3. Verify the mock of `handle_workflow_failure` receives both renamed/new kwargs

**Note:** The assertions in `test_failure_handling.py` that check `call_kwargs["update_labels"]`
from `core.py` call sites won't break in this step (mocks intercept at the module level).
Those assertions update in step 6a when the call sites themselves change kwarg names.

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Implement Step 5: update handle_create_pr_failure() in create_pr/helpers.py.

1. Update tests FIRST in tests/workflows/create_pr/test_failure_handling.py:
   - Rename update_labels → update_issue_labels in all test calls
   - Add post_issue_comments where needed
2. Modify handle_create_pr_failure() in src/mcp_coder/workflows/create_pr/helpers.py:
   - Rename update_labels → update_issue_labels
   - Add post_issue_comments parameter
   - Pass both to handle_workflow_failure()
3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass

NOTE: Callers in create_pr/core.py still use update_labels — those are fixed in Step 6.
```

## COMMIT MESSAGE
```
feat: update create-pr helpers with split flags (#661)

Rename update_labels → update_issue_labels in handle_create_pr_failure().
Add post_issue_comments parameter and pass both to handle_workflow_failure().
```
