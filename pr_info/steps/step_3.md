# Step 3: Fix 5 bypass files to import through shim

## Context
See [summary.md](summary.md) for full issue context.

5 files import directly from `mcp_coder.utils.git_operations` instead of going through the `mcp_coder.mcp_workspace_git` shim. All must be routed through the shim for consistent architecture.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/utils/git_utils.py` | Modify import |
| `src/mcp_coder/utils/github_operations/base_manager.py` | Modify import |
| `src/mcp_coder/utils/github_operations/ci_results_manager.py` | Modify import |
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Modify import |
| `src/mcp_coder/utils/github_operations/issues/manager.py` | Modify import |

## WHAT

Pure import path changes — no logic, no signatures, no test changes needed (existing tests use mocking that patches at the destination module level).

## HOW

### File 1: `utils/git_utils.py`
```python
# BEFORE:
from mcp_coder.utils.git_operations.branch_queries import get_current_branch_name

# AFTER:
from mcp_coder.mcp_workspace_git import get_current_branch_name
```

### File 2: `utils/github_operations/base_manager.py`
```python
# BEFORE:
from mcp_coder.utils.git_operations.remotes import get_github_repository_url
from mcp_coder.utils.git_operations.repository_status import is_git_repository

# AFTER:
from mcp_coder.mcp_workspace_git import get_github_repository_url, is_git_repository
```

### File 3: `utils/github_operations/ci_results_manager.py`
```python
# BEFORE:
from mcp_coder.utils.git_operations.branch_queries import validate_branch_name

# AFTER:
from mcp_coder.mcp_workspace_git import validate_branch_name
```

### File 4: `utils/github_operations/pr_manager.py`
```python
# BEFORE:
from mcp_coder.utils.git_operations import (
    get_default_branch_name,
    get_github_repository_url,
)

# AFTER:
from mcp_coder.mcp_workspace_git import get_default_branch_name, get_github_repository_url
```

### File 5: `utils/github_operations/issues/manager.py`
```python
# BEFORE:
from mcp_coder.utils.git_operations.branch_queries import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)

# AFTER:
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
```

## ALGORITHM

No logic changes — pure import rewiring.

## DATA

No data structure changes.

## Test impact

No test changes required. Existing tests mock at the consuming module level (e.g., `@patch("mcp_coder.utils.github_operations.base_manager.is_git_repository")`), which continues to work regardless of where the import originates.

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_3.md.

Fix 5 files that bypass the git shim by importing directly from
mcp_coder.utils.git_operations. Change each to import from
mcp_coder.mcp_workspace_git instead:

1. src/mcp_coder/utils/git_utils.py — get_current_branch_name
2. src/mcp_coder/utils/github_operations/base_manager.py — get_github_repository_url, is_git_repository
3. src/mcp_coder/utils/github_operations/ci_results_manager.py — validate_branch_name
4. src/mcp_coder/utils/github_operations/pr_manager.py — get_default_branch_name, get_github_repository_url
5. src/mcp_coder/utils/github_operations/issues/manager.py — extract_issue_number_from_branch, get_current_branch_name

Run all checks (pylint, mypy, pytest) after changes.
```

## Commit message
```
refactor: route git imports through shim in 5 bypass files (#886)

Change 5 files that imported directly from
mcp_coder.utils.git_operations to import through
mcp_coder.mcp_workspace_git instead. This ensures all git
operations flow through the single shim entry point.
```
