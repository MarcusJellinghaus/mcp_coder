# Step 4: Update `__init__.py` — Docstring + Re-exports

## Context
See `pr_info/steps/summary.md` for the full architectural overview.
Steps 1–3 must be complete.
This step updates the package's public API to point to the new modules instead of `orchestrator`.

---

## WHERE

**Modify:** `src/mcp_coder/workflows/vscodeclaude/__init__.py`

---

## WHAT

Two changes to `__init__.py`:

### 1. Add module docstring (from `orchestrator.py`)

Move the ~310-line docstring that starts with `"""Session orchestration for vscodeclaude feature.` from `orchestrator.py` to the top of `__init__.py`, replacing the existing short docstring:

```python
# Before (existing __init__.py docstring):
"""VSCodeClaude session management utilities.

This module provides utilities for managing VSCode/Claude Code sessions
for interactive workflow stages.
"""

# After: the full ~310-line docstring from orchestrator.py
"""Session orchestration for vscodeclaude feature.
...
(full content)
...
"""
```

### 2. Update the Orchestration re-exports block

```python
# Before:
from .orchestrator import (
    get_stage_display_name,
    handle_pr_created_issues,
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
    truncate_title,
)

# After:
from .session_launch import (
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    regenerate_session_files,
)
from .session_restart import (
    handle_pr_created_issues,
    restart_closed_sessions,
)
```

Note: `get_stage_display_name` and `truncate_title` are re-exported from `orchestrator` but originate in `helpers.py`. Update their import to come directly from `.helpers`:

```python
# These were already re-exported via orchestrator — now import directly:
from .helpers import get_stage_display_name, truncate_title
```

Also add `regenerate_session_files` to `__all__` (it was not previously exported but is now a public function in its own module).

---

## HOW

The `__init__.py` `__all__` list must be updated to:
- Replace the `orchestrator` comment block with two separate comments
- Add `"regenerate_session_files"` to `__all__`
- Keep all other symbols unchanged

---

## ALGORITHM

```
1. Replace short __init__.py docstring with full docstring from orchestrator.py
2. Replace `from .orchestrator import (...)` with two imports:
   - from .session_launch import (launch_vscode, prepare_and_launch_session,
                                   process_eligible_issues, regenerate_session_files)
   - from .session_restart import (handle_pr_created_issues, restart_closed_sessions)
3. Change get_stage_display_name + truncate_title import to come from .helpers directly
4. Add "regenerate_session_files" to __all__
```

---

## DATA

No new data. `__init__.py` remains a re-export facade — no logic.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.
Steps 1–3 are complete.

Before making any changes, verify that no code imports `get_stage_display_name` or
`truncate_title` directly from `.orchestrator` (bypassing `__init__.py`).
Use mcp__filesystem__read_file to read these files and check their import blocks:
- src/mcp_coder/workflows/vscodeclaude/cleanup.py
- src/mcp_coder/workflows/vscodeclaude/sessions.py
- src/mcp_coder/workflows/vscodeclaude/status.py
- src/mcp_coder/workflows/vscodeclaude/helpers.py
- src/mcp_coder/workflows/vscodeclaude/workspace.py
- src/mcp_coder/cli/commands/coordinator/core.py
If any file imports these two functions directly from `.orchestrator`, fix those imports
before proceeding.

Modify `src/mcp_coder/workflows/vscodeclaude/__init__.py`:

1. Replace the existing short module docstring with the full ~310-line docstring
   from the top of `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
   (everything between the outer triple-quotes at lines 1 and ~313).

2. Replace the existing `from .orchestrator import (...)` block with:
   - from .session_launch import (launch_vscode, prepare_and_launch_session,
                                   process_eligible_issues, regenerate_session_files)
   - from .session_restart import (handle_pr_created_issues, restart_closed_sessions)
   - from .helpers import get_stage_display_name, truncate_title
     (these were previously re-exported through orchestrator but originate in helpers)

3. Add "regenerate_session_files" to __all__.

Do NOT touch orchestrator.py yet.

After making changes, run:
- mcp__code-checker__run_pylint_check (categories: error, fatal)
- mcp__code-checker__run_mypy_check
- mcp__code-checker__run_pytest_check (extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"])

Fix any import errors, but make no logic changes.
```
