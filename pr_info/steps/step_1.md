# Step 1: Base-branch source and missing-base helper

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`. Write the tests first, then the code. Keep `detect_base_branch`'s signature and return type unchanged. Run pylint, pytest (unit tests, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflow_utils/base_branch.py`
- `tests/workflow_utils/test_base_branch.py`

## WHAT

```python
class BaseBranchSource(Enum):
    ISSUE = "issue"
    PR = "pr"
    MERGE_BASE = "merge-base"
    DEFAULT = "default"

def detect_base_branch_with_source(
    project_dir: Path,
    current_branch: Optional[str] = None,
    issue_data: Optional[IssueData] = None,
) -> Optional[tuple[str, BaseBranchSource]]: ...

def detect_base_branch(...same signature...) -> Optional[str]:  # now delegates

def check_base_branch_on_origin(project_dir: Path, base_branch: str) -> Optional[str]: ...
```

## HOW

- Move the body of `detect_base_branch` into `detect_base_branch_with_source`; each successful detection returns `(branch, BaseBranchSource.X)`. Move the priority docstring with it.
- `detect_base_branch` becomes: `result = detect_base_branch_with_source(...)`; `return result[0] if result else None`.
- `check_base_branch_on_origin` imports `execute_command` from `mcp_coder.utils.subprocess_runner` (not from `mcp_coder_utils`; import-linter). No tach/import-linter changes are needed.
- Do not export the new names from `workflow_utils/__init__.py`; callers import from `workflow_utils.base_branch`.

## ALGORITHM

```
check_base_branch_on_origin(project_dir, base):
    result = execute_command(["git", "ls-remote", "--exit-code", "--heads", "origin", base], cwd=str(project_dir))
    if result.return_code == 0: return None
    detail = result.stderr.strip()
    return f"Base branch '{base}' not found on origin; create and push it first" + (f" ({detail})" if detail else "")
```

## DATA

- `detect_base_branch_with_source`: `(branch_name, BaseBranchSource)` or `None`.
- `check_base_branch_on_origin`: `None` if the branch exists on origin, else an error message string (always mentions the branch name and "origin").

## Tests (write first)

In `tests/workflow_utils/test_base_branch.py`, reusing the existing `mocks` fixture:
- Parametrized `detect_base_branch_with_source` test, one case per source: issue base set → `ISSUE`; PR found → `PR`; merge-base mock returns a branch → `MERGE_BASE` (patch `detect_parent_branch_via_merge_base` in the test); default only → `DEFAULT`.
- All detection fails → `None`.
- Existing `detect_base_branch` tests keep passing unchanged (delegation).
- `check_base_branch_on_origin`, patching `mcp_coder.workflow_utils.base_branch.execute_command`:
  - return code 0 → `None`; asserts the argv `["git", "ls-remote", "--exit-code", "--heads", "origin", "epic/x"]`.
  - return code 2 → message containing `epic/x` and `origin`.
  - return code 128 with stderr → message contains the stderr text.
