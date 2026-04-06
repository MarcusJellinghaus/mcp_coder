# Step 4: Failure handling + create-pr helpers — split flags, gate comments

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE

### Source files (2 files):
- `src/mcp_coder/workflow_utils/failure_handling.py` — modify `handle_workflow_failure()`
- `src/mcp_coder/workflows/create_pr/helpers.py` — modify `handle_create_pr_failure()`

### Test files (2 files):
- `tests/workflow_utils/test_failure_handling.py` — update existing tests, add new ones
- `tests/workflows/create_pr/test_failure_handling.py` — update existing tests

## WHAT

### Changes to `handle_workflow_failure()`

**Rename parameter:** `update_labels: bool = False` → `update_issue_labels: bool = False`

**Add parameter:** `post_issue_comments: bool = False`

**Behavior change:** Comment posting is now gated by `post_issue_comments` in addition to the existing issue-number check.

```python
def handle_workflow_failure(
    failure: WorkflowFailure,
    comment_body: str,
    project_dir: Path,
    from_label_id: str,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW — gates comment posting
    issue_number: int | None = None,
) -> None:
```

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

### failure_handling.py
- The internal logic changes from `needs_comment = resolved_issue_number is not None` to `needs_comment = post_issue_comments and resolved_issue_number is not None`
- The `needs_label_update = update_labels` becomes `needs_label_update = update_issue_labels`
- The IssueManager is only created if `needs_label_update or needs_comment`

### helpers.py
- Update the call to `handle_workflow_failure()` to pass `update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments`
- No changes to `format_failure_comment()` or `parse_pr_summary()` — they're unaffected

## ALGORITHM (pseudocode — failure_handling.py updated section)
```
# Existing: resolve issue number (unchanged)
needs_label_update = update_issue_labels
needs_comment = post_issue_comments and resolved_issue_number is not None
if needs_label_update or needs_comment:
    issue_manager = IssueManager(project_dir)
    if needs_label_update:
        issue_manager.update_workflow_label(...)
    if needs_comment:
        issue_manager.add_comment(resolved_issue_number, comment_body)
```

## DATA
- **Input changes:** `update_labels → update_issue_labels`, new `post_issue_comments` (both files)
- **Output:** unchanged (void functions with side effects)
- **Behavior:** comments are now only posted when `post_issue_comments=True` AND issue number is resolved

## TESTS

### Update existing + add new in `tests/workflow_utils/test_failure_handling.py`:

1. **`test_sets_label_when_update_labels_true`** → rename kwarg to `update_issue_labels=True`
2. **`test_skips_label_when_update_labels_false`** → rename kwarg to `update_issue_labels=False`
3. **`test_posts_comment_always`** → **RENAME** to `test_posts_comment_when_post_issue_comments_true` — add `post_issue_comments=True` kwarg, keep `update_issue_labels=False`
4. **`test_label_failure_does_not_raise`** → rename kwarg to `update_issue_labels=True`
5. **`test_skips_comment_when_post_issue_comments_false`** — `post_issue_comments=False` (default), issue number resolvable → `add_comment` NOT called
6. **`test_skips_comment_when_post_issue_comments_default`** — no `post_issue_comments` kwarg (defaults to False), issue number resolvable → `add_comment` NOT called
7. **`test_posts_comment_with_provided_issue_number_when_enabled`** — update existing `test_posts_comment_with_provided_issue_number` to add `post_issue_comments=True`
8. **`test_no_issue_manager_when_both_flags_false`** — both flags False, no issue number → IssueManager constructor NOT called

### Update existing in `tests/workflows/create_pr/test_failure_handling.py`:

1. All calls to `handle_create_pr_failure()` that pass `update_labels=...` → rename to `update_issue_labels=...`
2. Add `post_issue_comments=True` where tests verify comment posting behavior
3. Verify the mock of `handle_workflow_failure` receives both renamed/new kwargs

**Note:** The assertions in `test_failure_handling.py` that check `call_kwargs["update_labels"]`
from `core.py` call sites won't break in this step (mocks intercept at the module level).
Those assertions update in step 5 when the call sites themselves change kwarg names.

## WHY MERGED

Steps 4 and 5 (original plan) are merged because renaming `update_labels` in
`handle_workflow_failure()` without also updating the call site in `helpers.py`
would break mypy (wrong keyword argument). Both files must change in the same commit.

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4: update handle_workflow_failure() and handle_create_pr_failure().

1. Update tests FIRST:
   - tests/workflow_utils/test_failure_handling.py:
     - Rename update_labels kwargs to update_issue_labels
     - Add post_issue_comments kwarg where comments should be posted
     - Add new tests for comment gating behavior
   - tests/workflows/create_pr/test_failure_handling.py:
     - Rename update_labels → update_issue_labels in all test calls
     - Add post_issue_comments where needed

2. Modify source files:
   - src/mcp_coder/workflow_utils/failure_handling.py:
     - Rename update_labels → update_issue_labels
     - Add post_issue_comments parameter (default False)
     - Gate comment posting on post_issue_comments flag
   - src/mcp_coder/workflows/create_pr/helpers.py:
     - Rename update_labels → update_issue_labels
     - Add post_issue_comments parameter
     - Pass both to handle_workflow_failure()

3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass

NOTE: Callers in create_pr/core.py and implement/core.py still use update_labels —
those are fixed in Step 5. Tests for those callers mock at the module level,
so they won't break from this rename.
```

## COMMIT MESSAGE
```
feat: split failure handling into update_issue_labels and post_issue_comments (#661)

Rename update_labels → update_issue_labels in handle_workflow_failure()
and handle_create_pr_failure(). Add post_issue_comments parameter that
gates comment posting (previously only gated by issue number). Both
default to False.
```
