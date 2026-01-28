# Step 1: Move `branch_status.py` to Application Layer

## LLM Prompt

```
Read pr_info/steps/summary.md for context. Implement Step 1: Move branch_status.py from utils/ to workflow_utils/.

This step moves the branch_status module to the correct architectural layer and updates all imports.
```

## WHERE: File Paths

### Files to Move
- `src/mcp_coder/utils/branch_status.py` → `src/mcp_coder/workflow_utils/branch_status.py`
- `tests/utils/test_branch_status.py` → `tests/workflow_utils/test_branch_status.py`

### Files to Modify
- `src/mcp_coder/utils/__init__.py`
- `src/mcp_coder/workflow_utils/__init__.py`
- `src/mcp_coder/cli/commands/check_branch_status.py`
- `src/mcp_coder/workflows/implement/core.py`
- `tests/cli/commands/test_check_branch_status.py`
- `tests/workflows/implement/test_ci_check.py`
- `.importlinter` (may need test contract update)

## WHAT: Changes Required

### 1. Move Source File
```bash
git mv src/mcp_coder/utils/branch_status.py src/mcp_coder/workflow_utils/branch_status.py
```

### 2. Move Test File
```bash
git mv tests/utils/test_branch_status.py tests/workflow_utils/test_branch_status.py
```

### 3. Update `src/mcp_coder/utils/__init__.py`
Remove all branch_status imports and exports:
- Remove `from .branch_status import (...)` block
- Remove branch_status items from `__all__`

### 4. Update `src/mcp_coder/workflow_utils/__init__.py`
Add branch_status exports:
```python
from .branch_status import (
    BranchStatusReport,
    CI_FAILED,
    CI_NOT_CONFIGURED,
    CI_PASSED,
    CI_PENDING,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
    truncate_ci_details,
)
```
Add to `__all__`.

### 5. Update Import in `branch_status.py`
Change internal import from:
```python
from mcp_coder.utils.git_operations.branches import needs_rebase
```
to:
```python
from mcp_coder.utils.git_operations import needs_rebase
```
(This will be updated in Step 2 when needs_rebase moves to workflows)

### 6. Update CLI Command Import
In `src/mcp_coder/cli/commands/check_branch_status.py`:
```python
# OLD
from ...utils.branch_status import BranchStatusReport, collect_branch_status
# NEW
from ...workflow_utils.branch_status import BranchStatusReport, collect_branch_status
```

### 7. Update Workflow Import
In `src/mcp_coder/workflows/implement/core.py`:
```python
# OLD
from mcp_coder.utils.branch_status import get_failed_jobs_summary, truncate_ci_details
# NEW
from mcp_coder.workflow_utils.branch_status import get_failed_jobs_summary, truncate_ci_details
```

### 8. Update Test Imports
In `tests/cli/commands/test_check_branch_status.py`:
```python
# OLD
from mcp_coder.utils.branch_status import BranchStatusReport
# NEW
from mcp_coder.workflow_utils.branch_status import BranchStatusReport
```

In `tests/workflows/implement/test_ci_check.py`:
```python
# OLD
from mcp_coder.utils.branch_status import get_failed_jobs_summary, truncate_ci_details
# NEW
from mcp_coder.workflow_utils.branch_status import get_failed_jobs_summary, truncate_ci_details
```

In moved `tests/workflow_utils/test_branch_status.py`:
- Update ALL imports from `mcp_coder.utils.branch_status` to `mcp_coder.workflow_utils.branch_status`

## HOW: Integration Points

The module imports from:
- `mcp_coder.utils.git_operations` (needs_rebase, readers)
- `mcp_coder.utils.github_operations` (CIResultsManager, IssueManager)
- `mcp_coder.workflow_utils.task_tracker` (has_incomplete_work) - NOW SAME LAYER!

The module is imported by:
- `cli.commands.check_branch_status` (Layer 1 → Layer 2 ✓)
- `workflows.implement.core` (Layer 2 → Layer 2 ✓)

## DATA: No Changes to Data Structures

All exports remain the same:
- `BranchStatusReport` dataclass
- `CI_PASSED`, `CI_FAILED`, `CI_NOT_CONFIGURED`, `CI_PENDING` constants
- `collect_branch_status()` function
- `create_empty_report()` function
- `get_failed_jobs_summary()` function
- `truncate_ci_details()` function

## Success Criteria

- [ ] File moved: `src/mcp_coder/workflow_utils/branch_status.py` exists
- [ ] Test moved: `tests/workflow_utils/test_branch_status.py` exists
- [ ] Old files removed from `utils/`
- [ ] All imports updated
- [ ] `import-linter` passes for layered_architecture contract
- [ ] `tach check` passes
- [ ] All tests pass
