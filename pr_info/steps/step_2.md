# Step 2: Create `session_restart.py`

## Context
See `pr_info/steps/summary.md` for the full architectural overview.
Step 1 must be complete (`session_launch.py` exists).
This step extracts the five restart-related items from `orchestrator.py` into a new dedicated module.

---

## WHERE

**Create:** `src/mcp_coder/workflows/vscodeclaude/session_restart.py`

No test changes in this step — existing tests in `test_orchestrator_sessions.py` and `test_orchestrator_cache.py` still import from `orchestrator` and continue to pass because `orchestrator.py` still exists at this point.

---

## WHAT

Items to move verbatim from `orchestrator.py`:

| Item | Type | Note |
|---|---|---|
| `BranchPrepResult` | `NamedTuple` | Only used by the two functions below — kept here, not in `types.py` |
| `_prepare_restart_branch` | private function | `(folder_path, current_status, branch_manager, issue_number) -> BranchPrepResult` |
| `_build_cached_issues_by_repo` | private function | `(sessions) -> dict[str, dict[int, IssueData]]` |
| `restart_closed_sessions` | public function | `(cached_issues_by_repo=None) -> list[VSCodeClaudeSession]` |
| `handle_pr_created_issues` | public function | `(issues: list[IssueData]) -> None` |

---

## HOW

**Imports needed in `session_restart.py`** — take from `orchestrator.py`'s import block, keeping only what these items use, plus the new cross-module imports:

```python
import logging
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

from ...utils.github_operations.issues import (
    IssueBranchManager, IssueData, IssueManager, get_all_cached_issues,
)
from ...utils.subprocess_runner import CalledProcessError, CommandOptions, execute_subprocess
from ...utils.user_config import get_cache_refresh_minutes
from .config import _get_configured_repos          # ← will exist after Step 3; see note below
from .helpers import get_issue_status, get_repo_short_name_from_full, truncate_title
from .issues import (
    get_ignore_labels, get_linked_branch_for_issue,
    get_matching_ignore_label, is_status_eligible_for_session,
    status_requires_linked_branch,
)
from .sessions import (
    add_session, clear_vscode_process_cache, clear_vscode_window_cache,
    is_session_active, is_vscode_open_for_folder, load_sessions,
    update_session_pid, update_session_status,
)
from .session_launch import launch_vscode, regenerate_session_files   # ← cross-module import
from .status import get_folder_git_status
from .types import VSCodeClaudeSession
```

> **Note on `_get_configured_repos`**: In this step, temporarily import it from `.orchestrator` (where it still exists). Step 3 moves it to `config.py` and updates this import. This avoids a dependency on Step 3 being done first.

**`__all__`** for the new file:
```python
__all__ = [
    "BranchPrepResult",
    "restart_closed_sessions",
    "handle_pr_created_issues",
]
```

---

## ALGORITHM

```
# session_restart.py structure
1. Copy imports (trimmed to what these 5 items use)
2. Define BranchPrepResult NamedTuple (verbatim from orchestrator.py)
3. Define __all__
4. Paste _prepare_restart_branch() verbatim
5. Paste _build_cached_issues_by_repo() verbatim
6. Paste restart_closed_sessions() verbatim
   - Its inline `from .sessions import remove_session` stays as-is
7. Paste handle_pr_created_issues() verbatim
```

---

## DATA

```python
class BranchPrepResult(NamedTuple):
    should_proceed: bool
    skip_reason: str | None = None
    branch_name: str | None = None
```

All functions retain their existing signatures and return types.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Step 1 is complete: session_launch.py exists.

Create the file `src/mcp_coder/workflows/vscodeclaude/session_restart.py`.

Copy these items verbatim from `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`:
- BranchPrepResult (NamedTuple)
- _prepare_restart_branch
- _build_cached_issues_by_repo
- restart_closed_sessions
- handle_pr_created_issues

Key import changes from orchestrator.py:
- Add: from .session_launch import launch_vscode, regenerate_session_files
- Keep: from .orchestrator import _get_configured_repos  (temporary — Step 3 will update this)
- Remove: get_stage_display_name, truncate_title (not used here except handle_pr_created_issues uses truncate_title — keep that)
- Remove: imports only needed by session_launch functions

Do NOT modify any logic. Do NOT touch orchestrator.py yet.

After creating the file, run:
- mcp__code-checker__run_pylint_check (categories: error, fatal)
- mcp__code-checker__run_mypy_check

Fix any import errors found, but make no logic changes.
```
