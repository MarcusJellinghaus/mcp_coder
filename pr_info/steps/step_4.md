# Step 4: Add `_handle_workflow_failure()` and wire into `run_implement_workflow()`

## Context
See [summary.md](./summary.md) for full implementation overview.

This is the core step — centralized failure handling, label transitions at every exit, and improved error UX.

## WHERE
- `src/mcp_coder/workflows/implement/core.py` — add `_handle_workflow_failure()`, `_get_diff_stat()`, modify `run_implement_workflow()`
- `tests/workflows/implement/test_core.py` — add tests for failure handler and label transitions

## WHAT

### `_get_diff_stat(project_dir: Path) -> str`
```python
def _get_diff_stat(project_dir: Path) -> str:
    """Get git diff --stat for uncommitted changes. Returns empty string on error."""
```

### `_handle_workflow_failure(failure: WorkflowFailure, project_dir: Path) -> None`
```python
def _handle_workflow_failure(failure: WorkflowFailure, project_dir: Path) -> None:
    """Handle workflow failure: set label, post comment, log banner."""
```

### Changes to `run_implement_workflow()`

1. **On success** (existing success path, end of function): unconditionally call `update_workflow_label(from_label_id="implementing", to_label_id="code_review")`
2. **On failure** (each `return 1` after prerequisites): call `_handle_workflow_failure()` with appropriate `WorkflowFailure`
3. **Remove post-error progress display** (the `if error_occurred:` block that calls `log_progress_summary`)

## HOW

### Imports to add in core.py
```python
from mcp_coder.utils.subprocess_runner import TimeoutExpired
from mcp_coder.utils.git_operations.core import _safe_repo_context
from mcp_coder.utils.git_operations.branch_queries import extract_issue_number_from_branch

from .constants import FailureCategory, WorkflowFailure
```

### `_get_diff_stat` implementation
```python
def _get_diff_stat(project_dir: Path) -> str:
    try:
        with _safe_repo_context(project_dir) as repo:
            return repo.git.diff("--stat")
    except Exception:
        return ""
```

### `_handle_workflow_failure` implementation

## ALGORITHM (pseudocode)
```
def _handle_workflow_failure(failure, project_dir):
    # 1. Log failure banner
    logger.log(NOTICE, "=" * 60)
    logger.log(NOTICE, "IMPLEMENTATION FAILED")
    logger.log(NOTICE, f"Category: {failure.category.name}")
    logger.log(NOTICE, f"Stage: {failure.stage}")
    logger.log(NOTICE, f"Error: {failure.message}")
    if failure.tasks_total > 0:
        logger.log(NOTICE, f"Progress: {failure.tasks_completed}/{failure.tasks_total} tasks")
    diff_stat = _get_diff_stat(project_dir)
    if diff_stat:
        logger.log(NOTICE, "Uncommitted changes:")
        logger.log(NOTICE, diff_stat)
    logger.log(NOTICE, "=" * 60)

    # 2. Set failure label (non-blocking)
    try:
        issue_manager = IssueManager(project_dir)
        issue_manager.update_workflow_label(
            from_label_id="implementing",
            to_label_id=failure.category.value,
        )
    except Exception as e:
        logger.warning(f"Failed to update issue label: {e}")

    # 3. Post GitHub comment (non-blocking)
    try:
        branch_name = get_current_branch_name(project_dir)
        issue_number = extract_issue_number_from_branch(branch_name) if branch_name else None
        if issue_number:
            comment_body = _format_failure_comment(failure, diff_stat)
            issue_manager.add_comment(issue_number, comment_body)
    except Exception as e:
        logger.warning(f"Failed to post failure comment: {e}")
```

### GitHub comment format
```markdown
## Implementation Failed
**Category:** {category name}
**Stage:** {stage}
**Error:** {message}
**Progress:** {completed}/{total} tasks completed

### Uncommitted Changes
```
{diff_stat or "No uncommitted changes"}
```
```

### Wiring into `run_implement_workflow()`

Map each error exit to a `WorkflowFailure`:

| Exit point | Category | Stage |
|-----------|----------|-------|
| `prepare_task_tracker` fails | GENERAL | "Task tracker preparation" |
| `process_single_task` returns `"error"` | GENERAL | "Task implementation" |
| `process_single_task` returns `"timeout"` | LLM_TIMEOUT | "Task implementation" |
| Final mypy check → formatting fails | GENERAL | "Post-implementation formatting" |
| Final mypy commit/push fails | GENERAL | "Post-implementation commit" |
| `check_and_fix_ci` returns False | CI_FIX_EXHAUSTED | "CI pipeline fix" |

**Prerequisite failures** (`check_git_clean`, `check_main_branch`, `check_prerequisites`): NO label change — just `return 1` as before.

**Success path**: Always call `update_workflow_label(from_label_id="implementing", to_label_id="code_review")`. This replaces the old conditional `if update_labels` block.

## DATA
- `_get_diff_stat()` returns `str` (may be empty)
- `_handle_workflow_failure()` returns `None` — all errors are caught internally
- GitHub comment is plain markdown

## TESTS (write first)

```python
class TestHandleWorkflowFailure:
    """Tests for _handle_workflow_failure."""

    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_sets_failure_label(self, mock_diff, mock_issue_cls):
        """Failure handler sets the correct label."""
        mock_diff.return_value = ""
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test", message="failed"
        )
        _handle_workflow_failure(failure, Path("/project"))

        mock_manager.update_workflow_label.assert_called_once_with(
            from_label_id="implementing",
            to_label_id="implementing_failed",
        )

    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    @patch("mcp_coder.workflows.implement.core.extract_issue_number_from_branch")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_posts_github_comment(self, mock_branch, mock_extract, mock_diff, mock_issue_cls):
        """Failure handler posts comment with failure details."""
        mock_branch.return_value = "189-feature"
        mock_extract.return_value = 189
        mock_diff.return_value = "file.py | 3 +++"
        mock_manager = MagicMock()
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="Task implementation", message="timed out",
            tasks_completed=2, tasks_total=5,
        )
        _handle_workflow_failure(failure, Path("/project"))

        mock_manager.add_comment.assert_called_once()
        comment = mock_manager.add_comment.call_args[0][1]
        assert "Implementation Failed" in comment
        assert "LLM Timeout" in comment or "LLM_TIMEOUT" in comment
        assert "2/5" in comment
        assert "file.py" in comment

    @patch("mcp_coder.workflows.implement.core.IssueManager")
    @patch("mcp_coder.workflows.implement.core._get_diff_stat")
    def test_label_error_non_blocking(self, mock_diff, mock_issue_cls):
        """Label update failure should not raise."""
        mock_diff.return_value = ""
        mock_manager = MagicMock()
        mock_manager.update_workflow_label.side_effect = Exception("API error")
        mock_issue_cls.return_value = mock_manager

        failure = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="failed"
        )
        # Should not raise
        _handle_workflow_failure(failure, Path("/project"))

    def test_prerequisite_failures_dont_change_labels(self):
        """Prerequisite failures should return 1 without calling failure handler."""
        # Test via run_implement_workflow — mock check_git_clean to return False
        # Verify IssueManager is never instantiated
        ...

class TestRunImplementWorkflowLabelTransitions:
    """Test that labels always transition on success/failure."""

    def test_success_always_updates_label_to_code_review(self):
        """On success, label transitions to code_review unconditionally."""
        ...

    def test_ci_exhaustion_sets_ci_fix_needed_label(self):
        """When CI fix attempts exhausted, sets ci_fix_needed label."""
        ...

    def test_timeout_sets_llm_timeout_label(self):
        """When LLM times out, sets llm_timeout label."""
        ...
```

## LLM PROMPT
```
Implement Step 4 of issue #189 (see pr_info/steps/summary.md for context).

Add `_get_diff_stat()` and `_handle_workflow_failure()` to core.py.
Wire `_handle_workflow_failure()` into every error exit in `run_implement_workflow()`.
Add unconditional label transition to code_review on success.
Remove the post-error log_progress_summary calls.

Write tests first in test_core.py, then implement.
See pr_info/steps/step_4.md for exact function signatures, algorithm,
wiring table, and test cases.
Run all quality checks after changes.
```
