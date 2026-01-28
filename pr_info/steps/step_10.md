# Step 10: Code Review Fixes (Second Round)

## LLM Prompt

```
You are implementing Step 10 of the vscodeclaude feature. Read pr_info/steps/summary.md for context.

This step addresses issues found in the second code review round. Make the following changes:

1. Add stale check to restart_closed_sessions() - skip sessions where issue status changed
2. Add validation to _get_repo_full_name() - raise ValueError if repo URL cannot be parsed
3. Remove unused issue_manager parameter from handle_pr_created_issues()
4. Remove redundant import json from test method (line ~306)
5. Remove empty TestIntegration class from tests
6. Standardize type hints to modern Python 3.9+ syntax throughout vscodeclaude.py

After changes, run all code quality checks and fix any issues.
```

## Overview

Fix issues identified in the second code review to improve code quality, consistency, and correctness.

---

## Task 1: Add Stale Check to restart_closed_sessions

### WHERE
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Update `restart_closed_sessions()` to skip stale sessions.

### HOW
Add `is_session_stale()` check before restarting a session.

### ALGORITHM
```
for session in sessions:
    if vscode_running: continue
    if folder_missing: remove_session, continue
    if is_session_stale(session): skip with log message, continue  # NEW
    if workspace_missing: warn, continue
    relaunch_vscode()
```

### DATA
- No signature change
- Behavior change: stale sessions are skipped instead of restarted

---

## Task 2: Add Validation to _get_repo_full_name

### WHERE
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Validate that repo URL parsing succeeds, raise ValueError if not.

### HOW
Check if result would be "unknown/repo" and raise ValueError with helpful message.

### ALGORITHM
```
def _get_repo_full_name(repo_config):
    repo_url = repo_config.get("repo_url", "")
    if "/" in repo_url:
        parts = parse_url(repo_url)
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    raise ValueError(f"Cannot parse repo URL: {repo_url}")  # NEW
```

### DATA
- Raises `ValueError` instead of returning "unknown/repo"

---

## Task 3: Remove Unused issue_manager Parameter

### WHERE
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Remove the unused `issue_manager` parameter from `handle_pr_created_issues()`.

### HOW
1. Remove parameter from function signature
2. Update all call sites (in `process_eligible_issues`)

### CURRENT SIGNATURE
```python
def handle_pr_created_issues(
    issues: list[IssueData],
    issue_manager: IssueManager,  # noqa: ARG001
) -> None:
```

### NEW SIGNATURE
```python
def handle_pr_created_issues(issues: list[IssueData]) -> None:
```

---

## Task 4: Remove Redundant Import in Tests

### WHERE
- `tests/cli/commands/coordinator/test_vscodeclaude.py`

### WHAT
Remove redundant `import json` inside test method.

### HOW
Delete the local import since `json` is already imported at module level.

---

## Task 5: Remove Empty TestIntegration Class

### WHERE
- `tests/cli/commands/coordinator/test_vscodeclaude.py`

### WHAT
Remove the `TestIntegration` class with empty placeholder tests.

### HOW
Delete the entire class (approximately lines 449-466).

---

## Task 6: Standardize Type Hints

### WHERE
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Convert all type hints from `typing` module style to modern Python 3.9+ style.

### HOW
Replace:
- `List[X]` → `list[X]`
- `Dict[X, Y]` → `dict[X, Y]`
- `Set[X]` → `set[X]`
- `Optional[X]` → `X | None`
- `Tuple[X, Y]` → `tuple[X, Y]`

Remove unused imports from `typing` module.

### EXAMPLE
```python
# Before
from typing import Any, List, Optional, TypedDict, cast

def foo(items: List[str]) -> Optional[str]:
    pass

# After
from typing import Any, TypedDict, cast

def foo(items: list[str]) -> str | None:
    pass
```

---

## Verification

After all changes:
1. Run `mcp__code-checker__run_pylint_check`
2. Run `mcp__code-checker__run_pytest_check` with `-n auto` and exclusion markers
3. Run `mcp__code-checker__run_mypy_check`
4. Fix any issues found
