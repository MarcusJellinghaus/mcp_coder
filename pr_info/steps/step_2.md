# Step 2: Update all callers and remove old exports

## Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md before starting.

`branch_status.py` has been moved to `src/mcp_coder/checks/branch_status.py` (step 1).
Now update every file that still imports from the old location.

Tasks (in order):

1. `src/mcp_coder/workflow_utils/__init__.py`
   - Remove the entire `from .branch_status import (...)` block
   - Remove all branch_status symbols from `__all__`
   - Do NOT add re-exports or backward-compat shims.

2. `src/mcp_coder/cli/commands/check_branch_status.py`
   - Change: `from ...workflow_utils.branch_status import BranchStatusReport, collect_branch_status`
   - To:     `from ...checks.branch_status import BranchStatusReport, collect_branch_status`

3. `src/mcp_coder/workflows/implement/core.py`
   - Change: `from mcp_coder.workflow_utils.branch_status import (get_failed_jobs_summary, truncate_ci_details,)`
   - To:     `from mcp_coder.checks.branch_status import (get_failed_jobs_summary, truncate_ci_details,)`

4. `tests/cli/commands/test_check_branch_status.py`
   - Change: `from mcp_coder.workflow_utils.branch_status import BranchStatusReport`
   - To:     `from mcp_coder.checks.branch_status import BranchStatusReport`

5. `docs/architecture/architecture.md`
   - Find the line referencing `workflow_utils/branch_status.py` (Branch status section)
   - Update it to reference `checks/branch_status.py`

Verify: Run the full test suite and confirm all tests pass.
Do NOT change any logic in any of these files.
```

---

## WHERE
| File | Change type |
|---|---|
| `src/mcp_coder/workflow_utils/__init__.py` | Remove branch_status block |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Update one import |
| `src/mcp_coder/workflows/implement/core.py` | Update one import |
| `tests/cli/commands/test_check_branch_status.py` | Update one import |
| `docs/architecture/architecture.md` | Update one reference line |

## WHAT

### `workflow_utils/__init__.py` — remove this block entirely:
```python
# REMOVE these lines:
from .branch_status import (
    CI_FAILED,
    CI_NOT_CONFIGURED,
    CI_PASSED,
    CI_PENDING,
    BranchStatusReport,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
    truncate_ci_details,
)
# AND remove all branch_status symbols from __all__
```

### `cli/commands/check_branch_status.py` — one-line change:
```python
# Before:
from ...workflow_utils.branch_status import BranchStatusReport, collect_branch_status
# After:
from ...checks.branch_status import BranchStatusReport, collect_branch_status
```

### `workflows/implement/core.py` — one-line change:
```python
# Before:
from mcp_coder.workflow_utils.branch_status import (
    get_failed_jobs_summary,
    truncate_ci_details,
)
# After:
from mcp_coder.checks.branch_status import (
    get_failed_jobs_summary,
    truncate_ci_details,
)
```

### `tests/cli/commands/test_check_branch_status.py` — one-line change:
```python
# Before:
from mcp_coder.workflow_utils.branch_status import BranchStatusReport
# After:
from mcp_coder.checks.branch_status import BranchStatusReport
```

## HOW
No new integration points. Each change is a single import path substitution.
The `workflow_utils` package retains all its other exports (`detect_base_branch`,
task tracker symbols, commit operations) unchanged.

## ALGORITHM
```
for each caller file:
    locate the import line referencing workflow_utils.branch_status
    replace "workflow_utils.branch_status" with "checks.branch_status"
    save file

in workflow_utils/__init__.py:
    remove the from .branch_status import (...) block
    remove branch_status names from __all__
    save file
```

## DATA
No data structure changes. Same public symbols, now imported from new path.

## Verification
```
pytest tests/ -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"
```
All tests must pass with zero import errors.
