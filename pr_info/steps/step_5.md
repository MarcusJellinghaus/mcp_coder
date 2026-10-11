# Step 5: Implement workflow's rebase step checks the base branch

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`. Step 1's `check_base_branch_on_origin` is already in place. This step must never fail the workflow: on a missing base it warns and returns `False`. Write the tests first, then the code. Run pylint, pytest (unit tests, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflow_steps/rebase.py`
- `tests/workflow_steps/test_rebase.py`

## WHAT

`_attempt_rebase_and_push(project_dir: Path) -> bool` — signature unchanged.

## HOW

- Import `check_base_branch_on_origin` alongside `detect_base_branch`.
- Inside `if target:`, before `rebase_onto_branch`:
  ```python
  missing_err = check_base_branch_on_origin(project_dir, target)
  if missing_err:
      logger.warning("Skipping rebase: %s", missing_err)
      return False
  ```
- Add the missing-base case to the docstring's `Returns: False if ...` list.

## ALGORITHM

```
if dirty: warn, return False
target = _get_rebase_target_branch()
if not target: return False
if err := check_base_branch_on_origin(target): warn, return False
rebase, push
```

## DATA

`bool` as today.

## Tests (write first)

In `test_rebase.py`:
- Existing tests that reach `rebase_onto_branch` (target detected, clean tree): patch `mcp_coder.workflow_steps.rebase.check_base_branch_on_origin` to return `None`. A module-level `autouse` fixture is acceptable if many tests need it; the new test then overrides it.
- New: clean tree, target `"epic/x"`, check returns an error → result `False`, `rebase_onto_branch` and `push_changes` not called, a WARNING record contains `epic/x`.
