# Step 12: Use Existing Issue Cache in vscodeclaude

## LLM Prompt

```
You are implementing Step 12 of the vscodeclaude feature. Read pr_info/steps/summary.md for context.

This step integrates the existing issue cache (`get_all_cached_issues()`) into the vscodeclaude feature
to eliminate the 90+ second delays caused by fetching ALL issues via `list_issues()`.

Key principle: Use the SAME cache that `coordinator run` uses. No new cache infrastructure.

The pattern is:
1. Call `get_all_cached_issues()` once per repo at the start
2. Filter locally with `_filter_eligible_vscodeclaude_issues()`
3. Pass cached issues dict to functions that need issue data (staleness checks, file regeneration)

After changes, run all code quality checks and fix any issues.
```

## Overview

Replace direct `list_issues()` calls with the existing `get_all_cached_issues()` function to use the same cache infrastructure that `coordinator run` uses.

---

## Task 1: Add Cache-Aware Issue Filtering

### WHERE
- `src/mcp_coder/utils/vscodeclaude/issues.py`

### WHAT
Add `_filter_eligible_vscodeclaude_issues()` and `get_cached_eligible_vscodeclaude_issues()`.

### HOW
```python
from ..github_operations.issue_cache import get_all_cached_issues
```

### ALGORITHM (filter function)
```
1. Load labels config (human_action labels, ignore_labels)
2. For each issue in all_issues:
   a. Skip if state != "open"
   b. Skip if not exactly one human_action label
   c. Skip if has any ignore_label
   d. Skip if github_username not in assignees
3. Sort by VSCODECLAUDE_PRIORITY
4. Return filtered list
```

### DATA
```python
def _filter_eligible_vscodeclaude_issues(
    all_issues: list[IssueData],
    github_username: str,
) -> list[IssueData]:
    """Filter issues for vscodeclaude eligibility (same logic as get_eligible_vscodeclaude_issues)."""
    ...

def get_cached_eligible_vscodeclaude_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    github_username: str,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> list[IssueData]:
    """Get eligible vscodeclaude issues using cache.
    
    Thin wrapper that:
    1. Calls get_all_cached_issues() for cache operations
    2. Filters results using _filter_eligible_vscodeclaude_issues()
    3. Falls back to get_eligible_vscodeclaude_issues() on cache errors
    """
    ...
```

---

## Task 2: Update process_eligible_issues to Use Cache

### WHERE
- `src/mcp_coder/utils/vscodeclaude/orchestrator.py`

### WHAT
Replace `get_eligible_vscodeclaude_issues()` with `get_cached_eligible_vscodeclaude_issues()`.

### BEFORE
```python
eligible_issues = get_eligible_vscodeclaude_issues(issue_manager, github_username)
```

### AFTER
```python
from .issues import get_cached_eligible_vscodeclaude_issues
from ..github_operations.issue_cache import get_all_cached_issues
from ...cli.commands.coordinator.core import get_cache_refresh_minutes

# Get all cached issues once
repo_full_name = _get_repo_full_name(repo_config)
all_cached_issues = get_all_cached_issues(
    repo_full_name=repo_full_name,
    issue_manager=issue_manager,
    force_refresh=False,
    cache_refresh_minutes=get_cache_refresh_minutes(),
)

# Filter for vscodeclaude eligibility
eligible_issues = _filter_eligible_vscodeclaude_issues(all_cached_issues, github_username)
```

### RETURN VALUE
Also return the `all_cached_issues` dict (keyed by issue number) for use by callers.

---

## Task 3: Update execute_coordinator_vscodeclaude to Pass Cache

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT
1. Fetch cached issues once per repo at the start
2. Pass cached issues to `restart_closed_sessions()` and `process_eligible_issues()`

### ALGORITHM
```
1. For each repo:
   a. Create IssueManager
   b. Call get_all_cached_issues() ONCE
   c. Build issues_by_number dict: {issue_number: IssueData}
   d. Pass to restart_closed_sessions(cached_issues=issues_by_number)
   e. Pass to process_eligible_issues(cached_issues=issues_by_number)
```

---

## Task 4: Add Tests for Cache Integration

### WHERE
- `tests/utils/vscodeclaude/test_issues.py`

### WHAT
Add tests for `_filter_eligible_vscodeclaude_issues()` and `get_cached_eligible_vscodeclaude_issues()`.

### TEST CASES
1. `test_filter_eligible_vscodeclaude_issues_filters_correctly` - Same logic as existing filter tests
2. `test_get_cached_eligible_vscodeclaude_issues_uses_cache` - Verify cache is called
3. `test_get_cached_eligible_vscodeclaude_issues_fallback_on_error` - Verify fallback to direct fetch

---

## Task 5: Update __init__.py Exports

### WHERE
- `src/mcp_coder/utils/vscodeclaude/__init__.py`

### WHAT
Export new functions:
```python
from .issues import (
    get_eligible_vscodeclaude_issues,
    get_cached_eligible_vscodeclaude_issues,  # NEW
    _filter_eligible_vscodeclaude_issues,      # NEW (for testing)
    ...
)
```

---

## Verification

After all changes:
1. Run `mcp__code-checker__run_pytest_check` with `-n auto` and exclusion markers
2. Run `mcp__code-checker__run_pylint_check`
3. Run `mcp__code-checker__run_mypy_check`
4. Manually test with `mcp-coder --log-level debug coordinator vscodeclaude` to verify cache is used
5. Fix any issues found
