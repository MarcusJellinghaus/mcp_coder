# Step 1: Create `session_launch.py`

## Context
See `pr_info/steps/summary.md` for the full architectural overview.
This step extracts the four session-launching functions from `orchestrator.py` into a new dedicated module.

---

## WHERE

**Create:** `src/mcp_coder/workflows/vscodeclaude/session_launch.py`

No test changes in this step — existing tests in `test_orchestrator_launch.py` and `test_orchestrator_regenerate.py` still import from `orchestrator` and continue to pass because `orchestrator.py` still exists at this point.

---

## WHAT

Functions to move verbatim from `orchestrator.py`:

| Function | Signature |
|---|---|
| `launch_vscode` | `(workspace_file: Path) -> int` |
| `prepare_and_launch_session` | `(issue, repo_config, vscodeclaude_config, repo_vscodeclaude_config, branch_name, is_intervention) -> VSCodeClaudeSession` |
| `process_eligible_issues` | `(repo_name, repo_config, vscodeclaude_config, max_sessions, repo_filter) -> list[VSCodeClaudeSession]` |
| `regenerate_session_files` | `(session, issue) -> Path` |

---

## HOW

**Imports needed in `session_launch.py`** — take exactly from `orchestrator.py`'s import block, keeping only what these four functions use:

```python
import logging
import platform
import shutil
from pathlib import Path

from ...utils.github_operations.issues import (
    IssueBranchManager, IssueData, IssueManager, get_all_cached_issues,
)
from ...utils.subprocess_runner import (
    CalledProcessError, CommandOptions, execute_subprocess, launch_process,
)
from ...utils.user_config import get_cache_refresh_minutes
from .config import get_github_username, load_repo_vscodeclaude_config
from .helpers import (
    build_session, get_issue_status, get_repo_full_name, get_repo_short_name,
    get_repo_short_name_from_full, get_stage_display_name, truncate_title,
)
from .issues import (
    _filter_eligible_vscodeclaude_issues, get_linked_branch_for_issue,
    is_status_eligible_for_session, status_requires_linked_branch,
)
from .sessions import (
    add_session, get_active_session_count, get_session_for_issue,
)
from .types import (
    DEFAULT_PROMPT_TIMEOUT, RepoVSCodeClaudeConfig, VSCodeClaudeConfig, VSCodeClaudeSession,
)
from .workspace import (
    _remove_readonly, create_startup_script, create_status_file, create_vscode_task,
    create_working_folder, create_workspace_file, get_working_folder_path,
    run_setup_commands, setup_git_repo, update_gitignore,
    validate_mcp_json, validate_setup_commands,
)
```

**`__all__`** for the new file:
```python
__all__ = [
    "launch_vscode",
    "prepare_and_launch_session",
    "process_eligible_issues",
    "regenerate_session_files",
]
```

---

## ALGORITHM

```
# session_launch.py structure
1. Copy module-level imports (trimmed to only what these 4 functions use)
2. Define __all__ with the 4 public function names
3. Paste launch_vscode() verbatim
4. Paste prepare_and_launch_session() verbatim
5. Paste process_eligible_issues() verbatim
6. Paste regenerate_session_files() verbatim
```

---

## DATA

No new data structures. All functions retain their existing signatures and return types.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Create the file `src/mcp_coder/workflows/vscodeclaude/session_launch.py`.

Copy these four functions verbatim from `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`:
- launch_vscode
- prepare_and_launch_session
- process_eligible_issues
- regenerate_session_files

Use only the imports that these four functions actually need (listed in step_1.md).
Add __all__ listing the four function names.
Do NOT modify any logic. Do NOT touch orchestrator.py yet.

After creating the file, run:
- mcp__code-checker__run_pylint_check (categories: error, fatal)
- mcp__code-checker__run_mypy_check

Fix any import errors found, but make no logic changes.
```
