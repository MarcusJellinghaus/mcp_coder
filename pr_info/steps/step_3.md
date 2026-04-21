# Step 3 — Build `label_transitions.py` + migrate label update tests

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Extract `IssueManager.update_workflow_label()` into a standalone function in `workflow_utils/label_transitions.py`. Migrate the 11 label update tests from `tests/utils/github_operations/test_issue_manager_label_update.py` to `tests/workflow_utils/test_label_transitions.py`.

## WHERE

- `src/mcp_coder/workflow_utils/label_transitions.py` (new)
- `tests/workflow_utils/test_label_transitions.py` (new — migrated from `tests/utils/github_operations/test_issue_manager_label_update.py`)

## WHAT

### `label_transitions.py`

```python
def update_workflow_label(
    issue_manager: IssueManager,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
    validated_issue_number: Optional[int] = None,
) -> bool:
    """Workflow state machine transition.

    Reads labels.json via label_config, resolves internal_ids → label names,
    then delegates to issue_manager.transition_issue_label().
    """
```

### Dependencies

```python
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.mcp_workspace_github import IssueBranchManager, IssueManager
from mcp_coder.config.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
```

## HOW

The function is extracted from `IssueManager.update_workflow_label()` in `src/mcp_coder/utils/github_operations/issues/manager.py`. Key changes:
- `self` → `issue_manager` parameter
- `self.project_dir` → `issue_manager.project_dir`
- `self._repo_full_name` → `issue_manager._repo_full_name`
- `self.transition_issue_label(...)` → `issue_manager.transition_issue_label(...)`
- `IssueBranchManager(...)` construction stays the same
- Import paths updated to new locations (`config.label_config`, `mcp_workspace_git`)

## ALGORITHM

```
1. If validated_issue_number provided, use it directly (skip branch detection)
2. Else: detect branch name → extract issue number → verify branch linkage via IssueBranchManager
3. Load label config from labels.json via get_labels_config_path + load_labels_config
4. Build lookups, resolve from_label_id and to_label_id to label names
5. Compute labels_to_clear = all_workflow_names - {to_label_name}
6. Delegate to issue_manager.transition_issue_label(issue_number, to_label_name, labels_to_clear)
```

## DATA

- Input: `IssueManager` instance + label IDs + optional branch/issue params
- Output: `bool` (True on success, False on any failure — non-blocking)
- All exceptions caught and logged, never raised

## Test Migration

Migrate `TestIssueManagerLabelUpdate` class (11 tests) from `test_issue_manager_label_update.py`:

**Key changes in tests:**
- Import `update_workflow_label` from `mcp_coder.workflow_utils.label_transitions` instead of calling `manager.update_workflow_label(...)`
- Call pattern: `update_workflow_label(manager, "implementing", "code_review")` instead of `manager.update_workflow_label("implementing", "code_review")`
- Mock `mcp_coder.workflow_utils.label_transitions.load_labels_config` instead of `mcp_coder.utils.github_operations.issues.manager.load_labels_config`
- Mock `mcp_coder.workflow_utils.label_transitions.get_current_branch_name` instead of `mcp_coder.utils.github_operations.issues.manager.get_current_branch_name`
- The `transition_issue_label` method is what the new function calls (instead of going through `get_issue` + `set_labels`), so tests that mock `set_labels` need to be updated to mock `transition_issue_label` on IssueManager
- Tests that assert on `set_labels` call args need adaptation for `transition_issue_label` args

**Test list (all 11):**
1. `test_update_workflow_label_success_happy_path`
2. `test_update_workflow_label_invalid_branch_name`
3. `test_update_workflow_label_branch_not_linked`
4. `test_update_workflow_label_already_correct_state`
5. `test_update_workflow_label_missing_source_label`
6. `test_update_workflow_label_label_not_in_config`
7. `test_update_workflow_label_github_api_error`
8. `test_update_workflow_label_no_branch_provided`
9. `test_update_workflow_label_removes_different_workflow_label`
10. `test_update_workflow_label_with_validated_issue_number`
11. `test_update_workflow_label_validated_issue_number_invalid` (+ race condition test = 11 total, verify exact count)

## Commit

```
feat: rebuild update_workflow_label as standalone function
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 3 from pr_info/steps/step_3.md.

Extract update_workflow_label from IssueManager into a standalone function.
The behavior must be identical to the existing method.
Migrate the 11 tests, adapting mock targets to the new function location.
Both the old method and the new function should work simultaneously at this step.
Run all checks (pylint, mypy, pytest unit tests) after implementation.
```
