# Step 2: Extract CI operations to ci_operations.py

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #310

## WHERE

- `src/mcp_coder/workflows/implement/ci_operations.py` — **new file**
- `src/mcp_coder/workflows/implement/core.py` — remove CI functions, add import
- `tests/workflows/implement/test_ci_check.py` — update @patch paths and imports from core → ci_operations

## WHAT

Move these symbols from `core.py` to a new `ci_operations.py`:

| Symbol | Type | core.py lines |
|--------|------|---------------|
| `CIFixConfig` | dataclass | 106-114 |
| `_short_sha` | function | 117-128 |
| `_run_ci_analysis` | function | 185-262 |
| `_run_ci_fix` | function | 265-339 |
| `_poll_for_ci_completion` | function | 342-421 |
| `_wait_for_new_ci_run` | function | 424-462 |
| `_run_ci_analysis_and_fix` | function | 465-523 |
| `_read_problem_description` | function | 526-550 |
| `check_and_fix_ci` | function | 553-657 |

## HOW

### 1. Create ci_operations.py

Copy the 9 symbols listed above into the new file, preserving their exact code (move, don't change).

The new file needs these imports (subset of core.py's imports used by the moved functions):

```python
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from mcp_coder.checks.branch_status import get_failed_jobs_summary
from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.prompt_manager import get_prompt_with_substitutions
from mcp_coder.utils.git_operations.commits import get_latest_commit_sha
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.github_operations.ci_results_manager import (
    CIResultsManager,
    CIStatusData,
)

from .constants import (
    CI_MAX_FIX_ATTEMPTS,
    CI_MAX_POLL_ATTEMPTS,
    CI_NEW_RUN_MAX_POLL_ATTEMPTS,
    CI_NEW_RUN_POLL_INTERVAL_SECONDS,
    CI_POLL_INTERVAL_SECONDS,
    LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
    LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
    PR_INFO_DIR,
)
from .task_processing import (
    commit_changes,
    push_changes,
    run_formatters,
)
```

Add module docstring:
```python
"""CI check and fix operations for the implement workflow.

This module handles CI pipeline monitoring, failure analysis, and automated
fix attempts. Extracted from core.py for maintainability.
"""
```

Add logger: `logger = logging.getLogger(__name__)`

### 2. Update core.py

**Remove** the 9 symbols listed above from core.py.

**Add import** at the top of core.py (in the relative imports section):
```python
from .ci_operations import check_and_fix_ci
```

**Remove now-unused imports** from core.py. After removing the CI functions, these imports are no longer needed in core.py:
- `get_failed_jobs_summary` (only used by `_run_ci_analysis_and_fix`)
- `CIResultsManager`, `CIStatusData` (only used by CI functions)
- `get_latest_commit_sha` (only used by `check_and_fix_ci`)
- `CI_MAX_FIX_ATTEMPTS`, `CI_MAX_POLL_ATTEMPTS`, `CI_NEW_RUN_MAX_POLL_ATTEMPTS`, `CI_NEW_RUN_POLL_INTERVAL_SECONDS`, `CI_POLL_INTERVAL_SECONDS`, `LLM_CI_ANALYSIS_TIMEOUT_SECONDS` (only used by CI functions)

Keep in core.py (still used by remaining functions):
- `time` (used in `run_implement_workflow`)
- `get_prompt_with_substitutions` (used in `run_finalisation` after step 1)
- `PROMPTS_FILE_PATH` (used in `run_finalisation` and `prepare_task_tracker`)
- `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` — check if still used in core.py... It's used only in `_run_ci_fix`. **Remove from core.py imports.**
- `get_branch_name_for_logging` — used in `prepare_task_tracker` and `run_finalisation`. **Keep.**
- `store_session` — used in `prepare_task_tracker` and `run_finalisation`. **Keep.**

Also remove the `dataclass` import from core.py if `CIFixConfig` was the only dataclass defined there. Check: `core.py` line 12 imports `dataclass`, and `CIFixConfig` at line 106 is the only `@dataclass` in core.py. **Remove `from dataclasses import dataclass`.**

### 3. Update test_ci_check.py imports and @patch paths

`tests/workflows/implement/test_ci_check.py` has ~30+ `@patch("mcp_coder.workflows.implement.core.X")` decorators and direct imports from `core` for CI symbols (`_read_problem_description`, `CIResultsManager`, etc.). All patches and imports targeting CI symbols that moved to `ci_operations` must be updated:

- Change `from mcp_coder.workflows.implement.core import _read_problem_description` → `from mcp_coder.workflows.implement.ci_operations import _read_problem_description`
- Change all `@patch("mcp_coder.workflows.implement.core.X")` to `@patch("mcp_coder.workflows.implement.ci_operations.X")` where `X` is a symbol that moved (e.g., `CIResultsManager`, `time.sleep`, `prompt_llm`, `store_session`, `run_formatters`, `commit_changes`, `push_changes`, `get_failed_jobs_summary`, `get_latest_commit_sha`, `prepare_llm_environment`, `get_branch_name_for_logging`)

**Note**: Only update patches for symbols that are actually looked up in `ci_operations` at runtime. Symbols like `prompt_llm` are imported into `ci_operations`, so patches must target `ci_operations.prompt_llm` (not `core.prompt_llm`).

## DATA

No changes to function signatures or return types. All symbols moved as-is.

## ALGORITHM

```
1. Create ci_operations.py with required imports
2. Move 9 symbols (copy exact code, no modifications)
3. Add `from .ci_operations import check_and_fix_ci` to core.py
4. Remove moved symbols from core.py
5. Remove now-unused imports from core.py
6. Update test_ci_check.py: change imports and @patch paths from core → ci_operations for moved symbols
7. Update test_core.py: fix _poll_for_ci_completion import
```

## Tests

After this step, all tests should pass — including `test_ci_check.py` (updated in this step) and `test_core.py` (import fix below).

**Important**: To keep tests green within this step, also update the `_poll_for_ci_completion` import in test_core.py:

Change in `tests/workflows/implement/test_core.py` line 19:
```python
# Before:
from mcp_coder.workflows.implement.core import (
    ...
    _poll_for_ci_completion,
    ...
)

# After: remove _poll_for_ci_completion from this import
```

And add at the top of test_core.py:
```python
from mcp_coder.workflows.implement.ci_operations import _poll_for_ci_completion
```

This keeps the test file importable. The `TestPollForCiCompletionHeartbeat` class moves to `test_ci_operations.py` in Step 3.

## LLM Prompt

```
Implement Step 2 from pr_info/steps/step_2.md (see also pr_info/steps/summary.md).

Extract CI operations from core.py into a new ci_operations.py module. Move the 9 symbols listed in the step. Update imports in core.py and fix the _poll_for_ci_completion import in test_core.py.

No logic changes — only file location and imports change.

After changes: run pylint, pytest, mypy and fix any issues.
Write commit message to pr_info/.commit_message.txt.
```
