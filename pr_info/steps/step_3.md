# Step 3: Failure handling helpers (constants wiring + comment format + handler wrapper)

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## Goal
Add the failure handling infrastructure to the create_plan package: wire up `_format_failure_comment()` and `_handle_workflow_failure()` in `core.py`. These are private helpers that will be called by the orchestrator in step 4.

## WHERE

### Modified files
- `src/mcp_coder/workflows/create_plan/core.py` — add `_format_failure_comment()`, `_handle_workflow_failure()`, new imports

### Test files
- `tests/workflows/create_plan/test_main.py` — add tests for `_format_failure_comment` and `_handle_workflow_failure`

## WHAT

### New imports in `core.py`
```python
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure as SharedWorkflowFailure,
)
from mcp_coder.workflow_utils.failure_handling import (
    format_elapsed_time,
    get_diff_stat,
    handle_workflow_failure,
)
from .constants import FailureCategory, WorkflowFailure
```

### New function: `_format_failure_comment()`
```python
def _format_failure_comment(
    failure: WorkflowFailure,
    project_dir: Path,
) -> str:
    """Format GitHub comment for planning failure."""
```

**Returns**: Formatted markdown string.

### New function: `_handle_workflow_failure()`
```python
def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    issue_number: int,
    update_issue_labels: bool,
    post_issue_comments: bool,
) -> None:
    """Convert local WorkflowFailure to shared and delegate to shared handler."""
```

## HOW

### `_format_failure_comment` builds the comment body
Mirrors implement's pattern but adds `Prompt stage` field for LLM-stage failures.

### `_handle_workflow_failure` converts and delegates
Converts local `WorkflowFailure` (enum category) → shared `WorkflowFailure` (string category), then calls shared `handle_workflow_failure()`.

## ALGORITHM

### `_format_failure_comment`
```
1. Start with "## Planning Failed" header
2. Add "**Category:** <category.name title-cased>"
3. Add "**Stage:** <stage>"
4. Add "**Error:** <message>"
5. If prompt_stage is not None, add "**Prompt stage:** <N>"
6. If elapsed_time is not None, add "**Elapsed:** <formatted>"
7. Get diff_stat from project_dir; if non-empty, add "### Uncommitted Changes" section
8. Return joined lines
```

### `_handle_workflow_failure`
```
1. Build comment_body via _format_failure_comment(failure, project_dir)
2. Create SharedWorkflowFailure(category=failure.category.value, stage=failure.stage, message=failure.message, elapsed_time=failure.elapsed_time)
3. Call handle_workflow_failure(failure=shared, comment_body=comment, project_dir=project_dir, from_label_id="planning", update_issue_labels=..., post_issue_comments=..., issue_number=...)
```

## DATA

### Comment format example
```
## Planning Failed
**Category:** Llm Timeout
**Stage:** Prompt 2 (timeout)
**Error:** LLM request timed out after 600s
**Prompt stage:** 2
**Elapsed:** 10m 5s

### Uncommitted Changes
```<diff stat>```
```

### Comment format example (prereq, no prompt_stage)
```
## Planning Failed
**Category:** Prereq Failed
**Stage:** Prerequisites (git working directory not clean)
**Error:** Git working directory is not clean
**Elapsed:** 2s
```

## Tests

### `tests/workflows/create_plan/test_main.py` — new test class

```python
class TestFormatFailureComment:
    """Tests for _format_failure_comment."""

    def test_general_failure_comment(self):
        """Test comment format for general failure."""
        # Create WorkflowFailure with GENERAL category, no prompt_stage
        # Assert comment contains "## Planning Failed", category, stage, error
        # Assert "Prompt stage" NOT in comment

    def test_llm_timeout_with_prompt_stage(self):
        """Test comment format includes prompt stage for LLM timeout."""
        # Create WorkflowFailure with LLM_TIMEOUT, prompt_stage=2
        # Assert "**Prompt stage:** 2" in comment

    def test_elapsed_time_formatting(self):
        """Test elapsed time appears when provided."""
        # Create WorkflowFailure with elapsed_time=605.0
        # Assert "**Elapsed:** 10m 5s" in comment

    def test_no_elapsed_time_when_none(self):
        """Test elapsed time omitted when None."""
        # Create WorkflowFailure with elapsed_time=None
        # Assert "Elapsed" NOT in comment

    def test_uncommitted_changes_section(self):
        """Test diff stat section when uncommitted changes exist."""
        # Mock get_diff_stat to return " file1.py | 5 ++-\n"
        # Assert "### Uncommitted Changes" in comment

class TestHandleWorkflowFailure:
    """Tests for _handle_workflow_failure."""

    def test_calls_shared_handler_with_correct_args(self):
        """Test that shared handle_workflow_failure is called correctly."""
        # Mock handle_workflow_failure
        # Call _handle_workflow_failure with a local WorkflowFailure
        # Assert shared handler called with category=failure.category.value (string),
        # from_label_id="planning", correct flags

    def test_respects_update_issue_labels_flag(self):
        """Test that flags are passed through."""
        # Call with update_issue_labels=False, post_issue_comments=False
        # Assert shared handler called with same flags
```

## Commit message
```
feat(create_plan): add failure comment formatting and handler wrapper

Add _format_failure_comment() and _handle_workflow_failure() to
create_plan/core.py. These mirror implement's pattern:
- Comment format: ## Planning Failed with category, stage, error,
  optional prompt stage, elapsed time, and uncommitted changes
- Handler wrapper converts local FailureCategory enum to string
  and delegates to shared handle_workflow_failure()
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_3.md.

Key points:
- Add _format_failure_comment() and _handle_workflow_failure() to src/mcp_coder/workflows/create_plan/core.py
- Follow the pattern from src/mcp_coder/workflows/create_pr/helpers.py for reference
- Use the shared handle_workflow_failure from workflow_utils.failure_handling
- Always pass from_label_id="planning" to the shared handler
- Import WorkflowFailure as SharedWorkflowFailure (alias convention from implement)
- Add tests in tests/workflows/create_plan/test_main.py
- Run all quality checks (pylint, pytest, mypy) and fix any issues
```
