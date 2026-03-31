# Step 1: Create shared `workflow_utils/failure_handling.py` with tests

## Context
See `pr_info/steps/summary.md` for full issue context. This step extracts failure
handling utilities from `implement/core.py` into a shared module, with tests first (TDD).

## WHERE
- **Create:** `tests/workflow_utils/test_failure_handling.py`
- **Create:** `src/mcp_coder/workflow_utils/failure_handling.py`
- **Modify:** `src/mcp_coder/workflow_utils/__init__.py` (add exports)

## WHAT

### `failure_handling.py` — Functions and signatures:

```python
@dataclass(frozen=True)
class WorkflowFailure:
    category: str          # label ID in labels.json, e.g. "pr_creating_failed"
    stage: str             # e.g. "prerequisites", "cleanup"
    message: str           # human-readable error description
    elapsed_time: float | None = None


def get_diff_stat(project_dir: Path) -> str:
    """Get git diff --stat for uncommitted changes. Returns empty string on error."""


def format_elapsed_time(seconds: float) -> str:
    """Format seconds into '12m 34s' or '1h 5m 30s'."""


def handle_workflow_failure(
    failure: WorkflowFailure,
    comment_body: str,
    project_dir: Path,
    from_label_id: str,
    update_labels: bool = False,
    issue_number: int | None = None,
) -> None:
    """Handle workflow failure: log banner, set label, post comment.
    
    - Label update respects update_labels flag
    - Comment is always posted regardless of update_labels
    - issue_number: caller-provided, falls back to branch name extraction
    """
```

### `test_failure_handling.py` — Test classes:

```python
class TestFormatElapsedTime:
    # test_seconds_only: 45 → "45s"
    # test_minutes_and_seconds: 754 → "12m 34s"
    # test_hours_minutes_seconds: 3930 → "1h 5m 30s"
    # test_zero: 0 → "0s"

class TestGetDiffStat:
    # test_returns_diff_stat (mock _safe_repo_context)
    # test_returns_empty_on_error

class TestHandleWorkflowFailure:
    # test_logs_failure_banner
    # test_sets_label_when_update_labels_true (mock IssueManager)
    # test_skips_label_when_update_labels_false
    # test_posts_comment_always (even when update_labels=False)
    # test_posts_comment_with_provided_issue_number
    # test_extracts_issue_number_from_branch_when_not_provided
    # test_label_failure_does_not_raise
    # test_comment_failure_does_not_raise
```

## HOW
- Import `_safe_repo_context` from `mcp_coder.utils.git_operations.core`
- Import `IssueManager` from `mcp_coder.utils.github_operations.issues`
- Import `extract_issue_number_from_branch`, `get_current_branch_name` from branch_queries
- Add to `workflow_utils/__init__.py` exports

## ALGORITHM — `handle_workflow_failure`:
```
1. Log failure banner (category, stage, message)
2. If update_labels: try IssueManager.update_workflow_label(from_label_id → failure.category)
3. Resolve issue_number: use parameter if given, else extract from branch name
4. If issue_number: try IssueManager.add_comment(issue_number, comment_body)
5. All GitHub operations wrapped in broad try/except → log warning, never raise
```

## DATA
- `WorkflowFailure`: frozen dataclass with 4 fields
- `handle_workflow_failure` returns `None` (side effects only)
- `format_elapsed_time` returns `str`
- `get_diff_stat` returns `str`

## Commit
One commit: "Add shared workflow failure handling utilities with tests"
