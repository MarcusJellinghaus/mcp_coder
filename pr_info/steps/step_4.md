# Step 4: Failure handling + workflow cores — split into two flags

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE

### Source files (5 files):
- `src/mcp_coder/workflow_utils/failure_handling.py` — modify `handle_workflow_failure()`
- `src/mcp_coder/workflows/create_pr/helpers.py` — modify `handle_create_pr_failure()`
- `src/mcp_coder/workflows/implement/core.py` — rename param + add param
- `src/mcp_coder/workflows/create_pr/core.py` — rename param + add param
- `src/mcp_coder/workflows/create_plan.py` — rename param + add param

### Test files (5 files):
- `tests/workflow_utils/test_failure_handling.py` — update existing tests, add new ones
- `tests/workflows/create_pr/test_failure_handling.py` — update existing tests
- `tests/workflows/implement/test_core.py`
- `tests/workflows/create_pr/test_workflow.py`
- `tests/workflows/create_plan/test_main.py`

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

### Workflow function signature changes

**`run_implement_workflow()`:**
```python
def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- All internal calls to `handle_workflow_failure()` pass both flags
- Success-path label update uses `update_issue_labels`

**Internal wrapper `_handle_workflow_failure` (~line 160):** This wrapper accepts `update_labels` and
forwards it to the shared `handle_workflow_failure`. It MUST be renamed to `update_issue_labels` and
gain `post_issue_comments: bool = False`. There are ~9 call sites inside `run_implement_workflow`
that all pass `update_labels=update_labels` — each must be updated to pass both flags.

**`run_create_pr_workflow()`:**
```python
def run_create_pr_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- All internal calls to `_handle_create_pr_failure()` pass both flags
- Success-path label update uses `update_issue_labels`

**Internal call sites in `run_create_pr_workflow`:** ~8 calls to `_handle_create_pr_failure` pass
`update_labels=update_labels` — all must be updated to `update_issue_labels` and add
`post_issue_comments`. The success-path label check (`if update_labels:`) must also be renamed.

**`run_create_plan_workflow()`:**
```python
def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- Success-path label update uses `update_issue_labels`
- Note: `create_plan` doesn't currently use `handle_workflow_failure()` — `post_issue_comments` is accepted but not used internally yet (future-proofing the interface)

## HOW

### failure_handling.py
- The internal logic changes from `needs_comment = resolved_issue_number is not None` to `needs_comment = post_issue_comments and resolved_issue_number is not None`
- The `needs_label_update = update_labels` becomes `needs_label_update = update_issue_labels`
- The IssueManager is only created if `needs_label_update or needs_comment`

### helpers.py
- Update the call to `handle_workflow_failure()` to pass `update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments`
- No changes to `format_failure_comment()` or `parse_pr_summary()` — they're unaffected

### Workflow cores
- Rename `update_labels` parameter to `update_issue_labels` in all workflow function signatures
- Add `post_issue_comments: bool = False` parameter to all workflow function signatures
- Update all internal call sites to pass both flags

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
- **Workflow functions:** accept and forward both flags to failure handlers and success-path label updates

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
4. Update `run_create_pr_workflow(update_labels=...)` calls to use `update_issue_labels=...`
5. Update `call_kwargs["update_labels"]` assertions to use `call_kwargs["update_issue_labels"]`

### Update workflow tests:

In `test_core.py` (implement), `test_workflow.py` (create_pr), `test_main.py` (create_plan):
- Rename `update_labels=...` kwargs to `update_issue_labels=...`
- Add `post_issue_comments=...` where failure handling is tested
- Verify both flags reach `handle_workflow_failure` / `_handle_create_pr_failure`

## WHY MERGED

Steps 4 and 5 (original plan) are merged because renaming `update_labels` in
`handle_workflow_failure()` without also updating callers in `core.py` files
would break mypy (wrong keyword argument). All files must change in the same commit.

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4: update failure handling, create-pr helpers, and all workflow cores.

1. Update tests FIRST:
   - tests/workflow_utils/test_failure_handling.py:
     - Rename update_labels kwargs to update_issue_labels
     - Add post_issue_comments kwarg where comments should be posted
     - Add new tests for comment gating behavior
   - tests/workflows/create_pr/test_failure_handling.py:
     - Rename update_labels → update_issue_labels in all test calls
     - Update call_kwargs assertions
     - Add post_issue_comments where needed
   - tests/workflows/implement/test_core.py — rename update_labels → update_issue_labels, add post_issue_comments
   - tests/workflows/create_pr/test_workflow.py — same
   - tests/workflows/create_plan/test_main.py — same

2. Modify source files:
   - src/mcp_coder/workflow_utils/failure_handling.py:
     - Rename update_labels → update_issue_labels
     - Add post_issue_comments parameter (default False)
     - Gate comment posting on post_issue_comments flag
   - src/mcp_coder/workflows/create_pr/helpers.py:
     - Rename update_labels → update_issue_labels
     - Add post_issue_comments parameter
     - Pass both to handle_workflow_failure()
   - src/mcp_coder/workflows/implement/core.py — rename param + add param + update ~9 internal call sites
   - src/mcp_coder/workflows/create_pr/core.py — rename param + add param + update ~8 internal call sites
   - src/mcp_coder/workflows/create_plan.py — rename param + add param

3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: failure handling + workflow cores: split into two flags (#661)

Rename update_labels → update_issue_labels in handle_workflow_failure(),
handle_create_pr_failure(), and all workflow functions. Add
post_issue_comments parameter that gates comment posting. Update all
internal wrappers and call sites.
```
