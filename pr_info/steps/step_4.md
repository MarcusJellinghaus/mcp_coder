# Step 4: Make pre-PR `git_push()` fatal + add failure handling to `run_create_pr_workflow()`

## Context
See `pr_info/steps/summary.md` for full issue context. This is the main step:
wire up failure handling for all 7 failure points, add safety net, and make
pre-PR push fatal.

## WHERE
- **Modify:** `src/mcp_coder/workflows/create_pr/core.py` — `run_create_pr_workflow()`
- **Create:** `tests/workflows/create_pr/test_failure_handling.py` — tests for failure paths
- **Modify:** `tests/workflows/create_pr/test_workflow.py` — update existing tests

## WHAT

### New imports in `core.py`:
```python
import time
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    handle_workflow_failure,
    format_elapsed_time,
)
```

### New local function — `_format_failure_comment()`:
```python
def _format_failure_comment(
    stage: str,
    message: str,
    elapsed_time: float | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
) -> str:
    """Format a GitHub comment for a create-pr workflow failure."""
```

### New local function — `_handle_create_pr_failure()`:
```python
def _handle_create_pr_failure(
    stage: str,
    message: str,
    project_dir: Path,
    update_labels: bool,
    elapsed_time: float | None = None,
    issue_number: int | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
) -> None:
    """Convenience wrapper: format comment + call shared handler."""
```

### Changes to `run_create_pr_workflow()`:

1. **Add at top:** `start_time = time.time()`, `reached_terminal_state = False`
2. **Pre-PR push (step 3/5):** Change from warning to fatal `return 1` with failure handling
3. **Wrap all 7 `return 1` paths** with `_handle_create_pr_failure()` call + `reached_terminal_state = True`
4. **Add `try/finally`** block with safety net for unexpected exits
5. **Success path:** set `reached_terminal_state = True` before `return 0`

### Failure points wired up:

| # | Code location | Stage | Extra context |
|---|--------------|-------|---------------|
| 1 | `check_prerequisites()` returns False | `prerequisites` | — |
| 2 | `generate_pr_summary()` raises | `summary_generation` | — |
| 3 | `git_push()` fails before PR (NEW fatal) | `push` | — |
| 4 | `create_pull_request()` returns None | `pr_creation` | — |
| 5 | `cleanup_repository()` returns False | `cleanup` | pr_url, pr_number, is_cleanup=True |
| 6 | Commit cleanup changes fails | `cleanup` | pr_url, pr_number, is_cleanup=True |
| 7 | Push cleanup changes fails | `cleanup` | pr_url, pr_number, is_cleanup=True |

**Note on failure point #2:** The current code catches `(ValueError, FileNotFoundError)` from `generate_pr_summary()`. Broaden to `except Exception` so all failure types get the informative `summary_generation` stage rather than falling through to the safety net as "Unexpected exit".

### `test_failure_handling.py` — Test classes:
```python
class TestFormatFailureComment:
    # test_basic_failure_comment
    # test_comment_with_elapsed_time
    # test_comment_with_pr_link
    # test_cleanup_failure_notes_pr_info_exists

class TestCreatePrFailureHandling:
    # test_prerequisites_failure_sets_label_and_posts_comment
    # test_summary_generation_failure
    # test_push_failure_is_fatal (NEW - was warning before)
    # test_pr_creation_failure
    # test_cleanup_failure_includes_pr_link
    # test_cleanup_commit_failure
    # test_cleanup_push_failure
    # test_safety_net_fires_on_unexpected_exception
    # test_safety_net_skipped_on_normal_failure
    # test_comment_posted_even_when_update_labels_false
    # test_label_not_set_when_update_labels_false
```

## HOW
- All failure paths call `_handle_create_pr_failure()` which:
  1. Formats comment via `_format_failure_comment()`
  2. Calls shared `handle_workflow_failure()` with `from_label_id="pr_creating"`,
     `category="pr_creating_failed"`
- `issue_number` passed from `cached_issue_number` (already computed for label updates)
- Comment always posted regardless of `update_labels`

## ALGORITHM — `_format_failure_comment`:
```
1. Start with "## PR Creation Failed"
2. Add "**Stage:** {stage}"
3. Add "**Error:** {message}"
4. If elapsed_time: add "**Elapsed:** {format_elapsed_time(elapsed_time)}"
5. If pr_url: add "**PR:** [{pr_number}]({pr_url})"
6. If is_cleanup_failure: add note "pr_info/ directory may still exist on the branch"
```

## ALGORITHM — safety net in `finally`:
```
1. If not reached_terminal_state:
2.   elapsed = time.time() - start_time
3.   try: _handle_create_pr_failure("Unexpected exit", "...", ...)
4.   except: logger.error("Safety net also failed")
```

## DATA
- All failures use `category="pr_creating_failed"` (single category)
- `from_label_id="pr_creating"` (current label when workflow starts)
- `pr_info` dict (from step 3) passed to cleanup failures for PR link

## Commit
One commit: "Add failure handling to create-pr workflow with safety net"
