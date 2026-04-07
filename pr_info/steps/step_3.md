# Step 3: Failure handling helpers + orchestration wiring + CLI help

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## Goal
Add failure handling helpers (`_format_failure_comment`, `_handle_workflow_failure`) to `create_plan/core.py`, wire them into `run_create_plan_workflow()` and `run_planning_prompts()` at every failure point, promote commit/push to hard errors, and update the CLI help text. This is one cohesive commit because the helpers are dead code (vulture-flagged) until orchestration wires them in, and the CLI help text is a one-line change too small for its own commit.

## WHERE

### Modified files
- `src/mcp_coder/workflows/create_plan/core.py` — add `_format_failure_comment()`, `_handle_workflow_failure()`, modify `run_create_plan_workflow()` and `run_planning_prompts()`, new imports
- `src/mcp_coder/cli/parsers.py` — update `add_create_plan_parser()` help text

### Test files
- `tests/workflows/create_plan/test_main.py` — add tests for `_format_failure_comment`, `_handle_workflow_failure`, failure handling integration; update commit/push behavior tests
- `tests/workflows/create_plan/test_prompt_execution.py` — update `run_planning_prompts` tests for new return type

### Verified files (read-only check)
- `docs/configuration/config.md` — verify `update_issue_labels` and `post_issue_comments` rows are accurate (already accurate; no change expected)

## WHAT

### New imports in `core.py`
```python
import time  # module-level
from dataclasses import replace

from mcp_coder.llm.interface import LLMTimeoutError
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

Note: `import time` is module-level. The per-invocation `start_time = time.time()` is function-local inside `run_create_plan_workflow()`.

### New function: `_format_failure_comment()`
```python
def _format_failure_comment(
    failure: WorkflowFailure,
    diff_stat: str,
) -> str:
    """Format GitHub comment for planning failure."""
```

**Signature note**: Takes `diff_stat: str` directly (caller computes it). Matches implement's convention and simplifies tests — no need to mock `get_diff_stat` per test.

**Returns**: Formatted markdown string.

### New function: `_handle_workflow_failure()`
```python
def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_issue_labels: bool,
    post_issue_comments: bool,
) -> None:
    """Convert local WorkflowFailure to shared and delegate to shared handler."""
```

**Signature note**: No `issue_number` parameter — matches implement's pattern exactly. The shared `handle_workflow_failure()` auto-resolves issue_number from the current git branch.

### Changed function: `run_planning_prompts()`
**Old signature**: `(...) -> bool`
**New signature**: `(...) -> tuple[bool, WorkflowFailure | None]`

Returns `(True, None)` on success, `(False, WorkflowFailure(...))` on failure. Builds `WorkflowFailure` inline at each detection point to preserve prompt-stage info.

### Changed function: `run_create_plan_workflow()`
**Signature**: unchanged (returns `int`)
**Behavior changes**:
1. Add `start_time = time.time()` at the top (function-local; `import time` is module-level)
2. At each failure point, construct `WorkflowFailure` and call `_handle_workflow_failure()`
3. Commit/push failures: change from `logger.warning` + continue to hard error (return 1)
4. Wire `post_issue_comments` parameter through to `_handle_workflow_failure()`

### `parsers.py` — update create-plan command help
Change the `help` parameter of `add_parser("create-plan", ...)` from:
```python
help="Generate implementation plan for a GitHub issue"
```
to:
```python
help="Generate implementation plan for a GitHub issue (sets failure labels and posts comments on error)"
```

## HOW

### `_format_failure_comment` builds the comment body
Mirrors implement's pattern but adds `Prompt stage` field for LLM-stage failures. Caller computes `diff_stat` via `get_diff_stat(project_dir)` and passes it in.

### `_handle_workflow_failure` converts and delegates
1. Compute `diff_stat = get_diff_stat(project_dir)`
2. Build `comment_body = _format_failure_comment(failure, diff_stat)`
3. Convert local `WorkflowFailure` (enum category) → shared `SharedWorkflowFailure` (string category) via `category=failure.category.value`
4. Call shared `handle_workflow_failure(failure=shared, comment_body=..., project_dir=..., from_label_id="planning", update_issue_labels=..., post_issue_comments=...)`

### Failure point wiring in `run_create_plan_workflow()`

Each failure point follows this pattern:
```python
if not success:
    failure = WorkflowFailure(
        category=FailureCategory.PREREQ_FAILED,
        stage="Prerequisites (git working directory not clean)",
        message="...",
        elapsed_time=time.time() - start_time,
    )
    _handle_workflow_failure(failure, project_dir, update_issue_labels, post_issue_comments)
    return 1
```

### Frozen dataclass override
`WorkflowFailure` is `@dataclass(frozen=True)`, so direct mutation does NOT work. When the orchestrator needs to override `elapsed_time` on a failure returned from `run_planning_prompts()` (which sets `elapsed_time=None`), use `dataclasses.replace`:
```python
from dataclasses import replace
...
success, failure = run_planning_prompts(...)
if not success:
    assert failure is not None
    failure = replace(failure, elapsed_time=time.time() - start_time)
    _handle_workflow_failure(failure, project_dir, update_issue_labels, post_issue_comments)
    return 1
```

### Failure point → category + stage label mapping (from issue #336 §4)

| Code location | Stage label (exact string) | Category |
|---|---|---|
| `check_prerequisites` returns `(False, ...)` — git not clean | `"Prerequisites (git working directory not clean)"` | `PREREQ_FAILED` |
| `check_prerequisites` returns `(False, ...)` — issue not found | `"Prerequisites (issue not found)"` | `PREREQ_FAILED` |
| `manage_branch` returns `None` | `"Branch management (branch creation failed)"` | `PREREQ_FAILED` |
| `check_pr_info_not_exists` returns `False` | `"Workspace setup (pr_info/ already exists)"` | `PREREQ_FAILED` |
| `create_pr_info_structure` returns `False` | `"Workspace setup (directory creation failed)"` | `PREREQ_FAILED` |
| `run_planning_prompts` returns `(False, failure)` | From `WorkflowFailure.stage` | From `WorkflowFailure.category` |
| `validate_output_files` returns `False` | `"Output validation"` | `GENERAL` |
| `commit_all_changes` returns `success=False` | `"Commit & push"` | `GENERAL` |
| `git_push` returns `success=False` | `"Commit & push"` | `GENERAL` |

**Split `check_prerequisites` failure detection at the orchestrator level**: In `run_create_plan_workflow`, call `is_working_directory_clean(project_dir)` BEFORE `check_prerequisites()`. If the working directory is dirty, emit `WorkflowFailure(category=PREREQ_FAILED, stage="Prerequisites (git working directory not clean)", ...)`. Then call `check_prerequisites()` — if it returns `(False, _)`, emit `WorkflowFailure(category=PREREQ_FAILED, stage="Prerequisites (issue not found)", ...)`. This avoids modifying `check_prerequisites`'s signature.

### `run_planning_prompts()` failure detection

For each prompt (1, 2, 3):
```python
# Timeout detection
try:
    response = prompt_llm(...)
except LLMTimeoutError as e:
    return (False, WorkflowFailure(
        category=FailureCategory.LLM_TIMEOUT,
        stage=f"Prompt {n} (timeout)",
        message=str(e),
        prompt_stage=n,
        elapsed_time=None,  # elapsed computed by orchestrator via dataclasses.replace
    ))
except Exception as e:
    return (False, WorkflowFailure(
        category=FailureCategory.GENERAL,
        stage=f"Prompt {n}",
        message=str(e),
        prompt_stage=n,
    ))

# Empty response detection
if not response or not response.get("text"):
    return (False, WorkflowFailure(
        category=FailureCategory.GENERAL,
        stage=f"Prompt {n} (empty response)",
        message="Prompt returned empty response",
        prompt_stage=n,
    ))

# Missing session_id (prompt 1 only)
if not session_id:
    return (False, WorkflowFailure(
        category=FailureCategory.GENERAL,
        stage="Prompt 1 (empty response)",
        message="Prompt 1 did not return session_id",
        prompt_stage=1,
    ))
```

## ALGORITHM

### `_format_failure_comment`
```
1. Start with "## Planning Failed" header
2. Add "**Category:** <category.name title-cased>"
3. Add "**Stage:** <stage>"
4. Add "**Error:** <message>"
5. If prompt_stage is not None, add "**Prompt stage:** <N>"
6. If elapsed_time is not None, add "**Elapsed:** <format_elapsed_time(elapsed_time)>"
7. If diff_stat (passed in) is non-empty, add "### Uncommitted Changes" section with code block
8. Return joined lines
```

### `_handle_workflow_failure`
```
1. diff_stat = get_diff_stat(project_dir)
2. comment_body = _format_failure_comment(failure, diff_stat)
3. shared = SharedWorkflowFailure(
     category=failure.category.value,
     stage=failure.stage,
     message=failure.message,
     elapsed_time=failure.elapsed_time,
   )
4. handle_workflow_failure(
     failure=shared,
     comment_body=comment_body,
     project_dir=project_dir,
     from_label_id="planning",
     update_issue_labels=update_issue_labels,
     post_issue_comments=post_issue_comments,
   )
```

### `run_create_plan_workflow` failure wiring
```
1. start_time = time.time()  # function-local
2. At each failure point:
   a. Compute elapsed = time.time() - start_time
   b. Construct WorkflowFailure with appropriate category + exact stage string from mapping table
   c. Call _handle_workflow_failure(failure, project_dir, update_issue_labels, post_issue_comments)
   d. Return 1
3. For run_planning_prompts failures:
   a. Use dataclasses.replace to override elapsed_time with orchestrator's elapsed
   b. Call handler, return 1
4. For commit/push: REMOVE the old logger.warning + continue pattern,
   REPLACE with hard error + failure handling
```

## DATA

### Comment format example (LLM timeout, with diff stat)
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

### Comment format example (prereq, no prompt_stage, no diff stat)
```
## Planning Failed
**Category:** Prereq Failed
**Stage:** Prerequisites (git working directory not clean)
**Error:** Git working directory is not clean
**Elapsed:** 2s
```

### `run_planning_prompts` new return examples
```python
# Success
(True, None)

# Timeout on prompt 2
(False, WorkflowFailure(
    category=FailureCategory.LLM_TIMEOUT,
    stage="Prompt 2 (timeout)",
    message="LLM request timed out after 600s",
    prompt_stage=2,
))
```

## Tests

### `tests/workflows/create_plan/test_main.py` — new test classes

```python
class TestFormatFailureComment:
    """Tests for _format_failure_comment."""

    def test_general_failure_comment(self):
        # WorkflowFailure with GENERAL, no prompt_stage; pass diff_stat=""
        # Assert "## Planning Failed", category, stage, error in comment
        # Assert "Prompt stage" NOT in comment

    def test_llm_timeout_with_prompt_stage(self):
        # WorkflowFailure with LLM_TIMEOUT, prompt_stage=2; diff_stat=""
        # Assert "**Prompt stage:** 2" in comment

    def test_elapsed_time_formatting(self):
        # WorkflowFailure with elapsed_time=605.0
        # Assert "**Elapsed:** 10m 5s" in comment

    def test_no_elapsed_time_when_none(self):
        # elapsed_time=None — assert "Elapsed" NOT in comment

    def test_uncommitted_changes_section(self):
        # Pass diff_stat=" file1.py | 5 ++-\n"
        # Assert "### Uncommitted Changes" in comment

    def test_no_uncommitted_changes_section_when_empty(self):
        # diff_stat="" — assert "Uncommitted Changes" NOT in comment

class TestHandleWorkflowFailure:
    """Tests for _handle_workflow_failure."""

    def test_calls_shared_handler_with_correct_args(self):
        # Mock get_diff_stat and handle_workflow_failure
        # Call _handle_workflow_failure with a local WorkflowFailure
        # Assert shared handler called with category=failure.category.value (string),
        # from_label_id="planning", correct flags
        # Assert NO issue_number kwarg passed (auto-resolved by shared)

    def test_respects_flags(self):
        # Call with update_issue_labels=False, post_issue_comments=False
        # Assert shared handler called with same flags

class TestFailureHandling:
    """Integration tests for failure handling in run_create_plan_workflow."""

    def test_prerequisites_dirty_git_failure(self):
        # Mock is_working_directory_clean=False
        # Assert _handle_workflow_failure called with stage
        # "Prerequisites (git working directory not clean)" and PREREQ_FAILED
        # Assert result == 1

    def test_prerequisites_issue_not_found_failure(self):
        # Mock IssueManager to fail finding issue
        # Assert stage "Prerequisites (issue not found)", PREREQ_FAILED

    def test_branch_failure(self):
        # Stage "Branch management (branch creation failed)", PREREQ_FAILED

    def test_pr_info_exists_failure(self):
        # Stage "Workspace setup (pr_info/ already exists)", PREREQ_FAILED

    def test_pr_info_create_failure(self):
        # Stage "Workspace setup (directory creation failed)", PREREQ_FAILED

    def test_planning_timeout_failure(self):
        # run_planning_prompts returns (False, WorkflowFailure(LLM_TIMEOUT, ...))
        # Assert handler called with the timeout failure (elapsed_time replaced)

    def test_validate_output_failure(self):
        # Stage "Output validation", GENERAL

    def test_commit_failure(self):
        # Stage "Commit & push", GENERAL, result == 1

    def test_push_failure(self):
        # Stage "Commit & push", GENERAL, result == 1

    def test_handler_called_when_flags_false(self):
        # update_issue_labels=False, post_issue_comments=False
        # Assert _handle_workflow_failure still called (gates internally)
```

### Updated existing tests in `test_main.py`

1. **`test_main_commit_fails_continues`** → rename to `test_main_commit_fails_returns_error`
   - Change assertion: `assert result == 1` (was `== 0`)
   - Push should NOT be called (workflow exits before push)

2. **`test_main_push_fails_continues`** → rename to `test_main_push_fails_returns_error`
   - Change assertion: `assert result == 1` (was `== 0`)

### Updated tests in `test_prompt_execution.py`

All `run_planning_prompts` tests need updating for new return type:
- Success: `assert result == (True, None)` (was `assert result is True`)
- Failure: `assert result[0] is False` and `assert result[1] is not None` (was `assert result is False`)
- Add assertions on `result[1].category`, `result[1].stage`, `result[1].prompt_stage` for specific failure cases

### Docs verification (no change expected)
Read `docs/configuration/config.md` and verify the existing rows:
```
| `update_issue_labels` | boolean | Update GitHub issue labels on workflow success/failure | No | `false` |
| `post_issue_comments` | boolean | Post GitHub comments on workflow failure | No | `false` |
```
These are already accurate. No docs change expected.

## Commit message
```
feat(create_plan): add failure handling with comment + label updates

Add _format_failure_comment() and _handle_workflow_failure() helpers
to create_plan/core.py mirroring implement's pattern. Wire them into
run_create_plan_workflow() and run_planning_prompts() at every failure
point with the exact stage labels from issue #336 §4.

Change run_planning_prompts() return type to tuple[bool, Optional[WorkflowFailure]]
to preserve prompt-stage information for LLM failures. Use
dataclasses.replace to override elapsed_time when promoting failures
returned from run_planning_prompts.

Promote commit/push failures from warnings to hard errors. Wire the
post_issue_comments parameter through to failure comment posting.

Update CLI help text for create-plan to mention failure handling.
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_3.md.

Key points:
- Add _format_failure_comment(failure, diff_stat) and
  _handle_workflow_failure(failure, project_dir, update_issue_labels, post_issue_comments)
  to src/mcp_coder/workflows/create_plan/core.py
- Follow the pattern from src/mcp_coder/workflows/implement/ for reference
- _handle_workflow_failure has NO issue_number parameter — shared handler auto-resolves it
- _format_failure_comment takes diff_stat as a parameter (caller computes it)
- Use the shared handle_workflow_failure from workflow_utils.failure_handling
- Always pass from_label_id="planning"
- Import WorkflowFailure as SharedWorkflowFailure (alias convention from implement)
- Modify run_create_plan_workflow(): add start_time = time.time() (import time at module level),
  construct WorkflowFailure at each failure point per the mapping table with EXACT stage strings
- Import LLMTimeoutError from mcp_coder.llm.interface
- Change run_planning_prompts() return type to tuple[bool, Optional[WorkflowFailure]]
- Catch LLMTimeoutError separately from general Exception in prompt execution
- Use dataclasses.replace to override elapsed_time on failures from run_planning_prompts
  (WorkflowFailure is frozen)
- Promote commit/push from logger.warning to hard errors with failure handling
- Update CLI help text for create-plan in src/mcp_coder/cli/parsers.py (one-liner)
- Read docs/configuration/config.md to verify update_issue_labels/post_issue_comments rows
- Update existing tests (commit/push now return 1, run_planning_prompts returns tuple)
- Add new failure handling tests
- Run all quality checks (pylint, pytest, mypy, lint_imports, vulture) and fix any issues
```
