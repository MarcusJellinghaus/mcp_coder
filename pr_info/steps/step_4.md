# Step 4: Failure handling — split into two flags, gate comments

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/workflow_utils/failure_handling.py` — modify `handle_workflow_failure()`
- `tests/workflow_utils/test_failure_handling.py` — update existing tests, add new ones

## WHAT

### Changes to `handle_workflow_failure()`

**Rename parameter:** `update_labels: bool = False` → `update_issue_labels: bool = False`

**Add parameter:** `post_issue_comments: bool = False`

**Behavior change:** Comment posting is now gated by `post_issue_comments` instead of being unconditional.

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

## HOW
- The internal logic changes from `needs_comment = resolved_issue_number is not None` to `needs_comment = post_issue_comments and resolved_issue_number is not None`
- The `needs_label_update = update_labels` becomes `needs_label_update = update_issue_labels`
- The IssueManager is only created if `needs_label_update or needs_comment`

## ALGORITHM (pseudocode — updated section)
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
- **Input changes:** `update_labels → update_issue_labels`, new `post_issue_comments`
- **Output:** unchanged (void function with side effects)
- **Behavior:** comments are now only posted when `post_issue_comments=True` AND issue number is resolved

## TESTS (update existing + add new)

### Update existing tests in `TestHandleWorkflowFailure`:

1. **`test_sets_label_when_update_labels_true`** → rename kwarg to `update_issue_labels=True`
2. **`test_skips_label_when_update_labels_false`** → rename kwarg to `update_issue_labels=False`
3. **`test_posts_comment_always`** → **RENAME** to `test_posts_comment_when_post_issue_comments_true` — add `post_issue_comments=True` kwarg, keep `update_issue_labels=False`
4. **`test_label_failure_does_not_raise`** → rename kwarg to `update_issue_labels=True`

### Add new tests:

5. **`test_skips_comment_when_post_issue_comments_false`** — `post_issue_comments=False` (default), issue number resolvable → `add_comment` NOT called
6. **`test_skips_comment_when_post_issue_comments_default`** — no `post_issue_comments` kwarg (defaults to False), issue number resolvable → `add_comment` NOT called
7. **`test_posts_comment_with_provided_issue_number_when_enabled`** — update existing `test_posts_comment_with_provided_issue_number` to add `post_issue_comments=True`
8. **`test_no_issue_manager_when_both_flags_false`** — both flags False, no issue number → IssueManager constructor NOT called

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4: update handle_workflow_failure() in failure_handling.py.

1. Update tests FIRST in tests/workflow_utils/test_failure_handling.py:
   - Rename update_labels kwargs to update_issue_labels
   - Add post_issue_comments kwarg where comments should be posted
   - Add new tests for comment gating behavior
2. Modify handle_workflow_failure() in src/mcp_coder/workflow_utils/failure_handling.py:
   - Rename update_labels → update_issue_labels
   - Add post_issue_comments parameter (default False)
   - Gate comment posting on post_issue_comments flag
3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass

NOTE: This will cause failures in callers (create_pr/helpers.py, implement/core.py).
Those are fixed in Steps 5 and 6. For now, focus on failure_handling.py and its tests.
```

## COMMIT MESSAGE
```
feat: split failure handling into update_issue_labels and post_issue_comments (#661)

Rename update_labels → update_issue_labels in handle_workflow_failure().
Add post_issue_comments parameter that gates comment posting (previously
unconditional). Both default to False.
```
