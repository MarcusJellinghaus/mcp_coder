# Step 10 — `base_branch.py` consolidation onto upstream detection

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_10.md`. Implement step 10 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(base-branch): wrap upstream detect_base_branch_with_source`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `BaseBranchSource` and `detect_base_branch_with_source` (from `mcp_workspace.git_operations.base_branch`)
- `src/mcp_coder/workflow_utils/base_branch.py` — rewrite detection; delete local `BaseBranchSource`, `_detect_from_pr`, `_detect_from_issue`, `_detect_default_branch`
- `src/mcp_coder/workflows/rebase.py` — import `BaseBranchSource` from `mcp_coder.mcp_workspace_git` instead of `workflow_utils.base_branch`
- `tests/workflow_utils/test_base_branch.py`, `tests/workflows/rebase/test_guards.py`

Public signatures stay (callers: `create_pr/core.py`, `gh_tool`, `git_tool`, `review/steps`, `workflow_steps/rebase`, `workflows/rebase`, `workflow_utils/__init__`).

## WHAT

```python
from mcp_coder.mcp_workspace_git import (
    BaseBranchSource,
    extract_issue_number_from_branch,
    get_current_branch_name,
    probe_origin_branch,
)
from mcp_coder.mcp_workspace_git import (
    detect_base_branch_with_source as _upstream_detect_with_source,
)
from mcp_coder.mcp_workspace_github import IssueData, IssueManager, PullRequestManager


def _build_managers(
    project_dir: Path, current_branch: str, issue_data: IssueData | None
) -> tuple[PullRequestManager | None, IssueManager | None]:
    """Build each manager in its own try; None on failure (missing token = skip)."""


def detect_base_branch_with_source(
    project_dir: Path,
    current_branch: str | None = None,
    issue_data: IssueData | None = None,
) -> tuple[str, BaseBranchSource] | None: ...


def detect_base_branch(project_dir, current_branch=None, issue_data=None) -> str | None:
    result = detect_base_branch_with_source(project_dir, current_branch, issue_data)
    return result[0] if result else None      # unchanged
```

## ALGORITHM

```
current_branch = current_branch or get_current_branch_name(project_dir)
if current_branch is None: return None                      # detached HEAD
pr_manager   = try PullRequestManager(project_dir) except -> None (debug log)
issue_manager = None if issue_data is not None or extract_issue_number_from_branch(current_branch) is None
                else try IssueManager(project_dir=project_dir) except -> None (debug log)
return _upstream_detect_with_source(project_dir, current_branch, issue_data, pr_manager, issue_manager)
```

Construction is cheap (no network). Keep the module docstring's priority list; note that
upstream also checks a merge-base winner still exists on origin (network `ls-remote`).

## Tests (write first)

Patch `mcp_coder.workflow_utils.base_branch.{_upstream_detect_with_source, PullRequestManager, IssueManager, get_current_branch_name}`.

- both managers built and injected; returns upstream's tuple.
- `PullRequestManager` raises → `pr_manager=None` passed, no exception.
- `IssueManager` raises → `issue_manager=None` passed.
- `issue_data` given → `IssueManager` not constructed, `issue_data` forwarded.
- branch without issue number (e.g. `"feature-x"`) → `IssueManager` not constructed.
- `get_current_branch_name` → `None` → returns `None`, upstream not called.
- `detect_base_branch` returns only the branch / `None`.
- Delete tests of removed private helpers. Update any assert on `"merge-base"` to `"merge_base"`
  (e.g. the `_resolve_base_branch` message in `test_guards.py`) and imports of `BaseBranchSource`
  to come from `mcp_coder.mcp_workspace_git`.

## DATA

- `(branch, BaseBranchSource)` with upstream enum values `issue | pr | merge_base | default`.
