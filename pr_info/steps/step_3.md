# Step 3: create-plan checks the base branch before creating a branch

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`. Step 1's `check_base_branch_on_origin` is already in place. Write the tests first, then the code. Keep `manage_branch`'s return type (`Optional[str]`). Run pylint, pytest (unit tests, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/create_plan/prerequisites.py`
- `src/mcp_coder/workflows/create_plan/core.py`
- `tests/workflows/create_plan/test_branch_management.py`
- `tests/workflows/create_plan/test_failure_handling.py`

## WHAT

```python
class BaseBranchMissingError(Exception):
    """The issue's base branch does not exist on origin."""

def manage_branch(project_dir, issue_number, issue_title, base_branch=None) -> Optional[str]:
    # unchanged signature; may now raise BaseBranchMissingError
```

## HOW

- `prerequisites.py` imports `check_base_branch_on_origin` from `mcp_coder.workflow_utils.base_branch`.
- In `manage_branch`, in the `else` (no linked branch) path, before `create_remote_branch_for_issue`:
  ```python
  if base_branch:
      missing_err = check_base_branch_on_origin(project_dir, base_branch)
      if missing_err:
          raise BaseBranchMissingError(missing_err)
  ```
- Add `except BaseBranchMissingError: raise` before the existing broad `except Exception`.
- Update the `manage_branch` docstring (`Raises:`).
- `core.py` (Step 2 of the workflow, around the `manage_branch` call): import `BaseBranchMissingError` from `.prerequisites`, wrap the call:
  ```python
  try:
      branch_name = manage_branch(...)
  except BaseBranchMissingError as e:
      logger.error("%s", e)
      failure = WorkflowFailure(
          category=FAILURE_LABELS["prereq"],
          stage="Branch management (base branch missing)",
          message=str(e),
          elapsed_time=time.time() - start_time,
      )
      _handle_workflow_failure(failure, project_dir, update_issue_labels,
                               post_issue_comments, issue_number=issue_number)
      return 1
  ```
  The existing `branch_name is None` handling stays.

## ALGORITHM

```
manage_branch:
    linked = manager.get_linked_branches(issue)
    if linked: use linked[0]                      # no check: branch already exists
    else:
        if base_branch and (err := check(base)): raise BaseBranchMissingError(err)
        create_remote_branch_for_issue(...)
    checkout ...
```

## DATA

`manage_branch` → branch name or `None` (unchanged), or raises `BaseBranchMissingError(message)`.

## Tests (write first)

`test_branch_management.py` (class for the `base_branch` parameter):
- Existing tests that pass `base_branch` and create a new branch: patch `mcp_coder.workflows.create_plan.prerequisites.check_base_branch_on_origin` to return `None`.
- New: check returns an error → `pytest.raises(BaseBranchMissingError)`, `create_remote_branch_for_issue` not called.
- New: linked branch exists with `base_branch` set → check not called.
- New: no `base_branch` → check not called.

`test_failure_handling.py`:
- New: `manage_branch` patched with `side_effect=BaseBranchMissingError("Base branch 'epic/x' not found on origin...")` → workflow returns 1 and `_handle_workflow_failure` receives a `WorkflowFailure` whose `message` contains `epic/x`. Follow the existing test at line ~206 for the patch set.
