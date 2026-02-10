# Step 8: Extract CLI Logic to Helper Function

## Goal
Extract the eligible issues building and branch checking logic from `execute_coordinator_vscodeclaude_status()` into a reusable helper function to reduce code duplication and improve separation of concerns.

## Context
The CLI command `execute_coordinator_vscodeclaude_status()` in `commands.py` contains complex logic (lines 580-625) that:
- Loops through repos
- Loads configurations
- Creates issue and branch managers
- Filters eligible issues
- Checks for linked branches for status-04/07
- Builds the `issues_without_branch` set

This logic should be extracted to a helper function in `issues.py` for reusability.

## Files to Modify

### 1. `src/mcp_coder/workflows/vscodeclaude/issues.py`
**Add new function:**

```python
def build_eligible_issues_with_branch_check(
    repo_names: list[str],
) -> tuple[list[tuple[str, IssueData]], set[tuple[str, int]]]:
    """Build eligible issues list with branch requirement checking.
    
    Args:
        repo_names: List of repo config names from coordinator.repos
        
    Returns:
        Tuple of:
        - List of (repo_full_name, issue) tuples for eligible issues
        - Set of (repo_full_name, issue_number) tuples for issues
          that require but lack a linked branch
          
    This function:
    1. Loops through each repo
    2. Loads repo config and GitHub username
    3. Gets eligible vscodeclaude issues (cached)
    4. For status-04/07 issues, checks for linked branch
    5. Adds to issues_without_branch set if branch missing/multiple
    """
```

**Algorithm:**
```
FOR each repo_name in repo_names:
    TRY:
        Load repo_config, get repo_url and repo_full_name
        Load vscodeclaude_config, get github_username
        Get eligible issues using get_cached_eligible_vscodeclaude_issues()
        Create branch_manager for linked branch checks
        
        FOR each issue in eligible_issues:
            Add (repo_full_name, issue) to result list
            
            IF status_requires_linked_branch(issue_status):
                TRY get_linked_branch_for_issue()
                IF branch is None OR ValueError (multiple):
                    Add (repo_full_name, issue_number) to issues_without_branch
                    
    EXCEPT any error:
        Log warning and continue to next repo
        
RETURN (eligible_issues_list, issues_without_branch_set)
```

### 2. `src/mcp_coder/cli/commands/coordinator/commands.py`
**Refactor `execute_coordinator_vscodeclaude_status()`:**

Replace lines 580-625 with:
```python
from ....workflows.vscodeclaude.issues import (
    build_eligible_issues_with_branch_check,
    get_cached_eligible_vscodeclaude_issues,
    get_linked_branch_for_issue,
    status_requires_linked_branch,
)

# ... existing code ...

# Build eligible issues list and issues_without_branch set
eligible_issues, issues_without_branch = build_eligible_issues_with_branch_check(
    repo_names
)

# Use display_status_table from status.py
display_status_table(
    sessions=sessions,
    eligible_issues=eligible_issues,
    repo_filter=args.repo,
    cached_issues_by_repo=cached_issues_by_repo,
    issues_without_branch=issues_without_branch,
)
```

## Tests

### File: `tests/workflows/vscodeclaude/test_issues.py`

Add new test class:

```python
class TestBuildEligibleIssuesWithBranchCheck:
    """Tests for build_eligible_issues_with_branch_check()."""
    
    def test_returns_empty_for_no_repos(self, ...):
        """Empty repo list returns empty results."""
        
    def test_returns_eligible_issues(self, ...):
        """Returns eligible issues from all repos."""
        
    def test_identifies_status_04_without_branch(self, ...):
        """Issues at status-04 without linked branch added to set."""
        
    def test_identifies_status_07_without_branch(self, ...):
        """Issues at status-07 without linked branch added to set."""
        
    def test_handles_multiple_branches(self, ...):
        """Issues with multiple linked branches added to set."""
        
    def test_status_01_without_branch_not_in_set(self, ...):
        """status-01 issues without branch NOT added to set."""
        
    def test_continues_on_repo_error(self, ...):
        """Continues processing if one repo fails."""
```

## LLM Prompt

```
You are implementing Step 8 of issue #422 branch handling feature.

Reference: pr_info/steps/summary.md for full context
This step: pr_info/steps/step_8.md

Task: Extract CLI logic to helper function for better code reusability.

Implementation order:
1. Read the current implementation in src/mcp_coder/cli/commands/coordinator/commands.py (lines 580-625)
2. Create build_eligible_issues_with_branch_check() in src/mcp_coder/workflows/vscodeclaude/issues.py
3. Write tests in tests/workflows/vscodeclaude/test_issues.py
4. Refactor CLI command to use the new helper
5. Run all quality checks (pylint, pytest, mypy)

Follow the algorithm and signatures exactly as specified in step_8.md.
Use MCP tools exclusively (no Read/Write/Edit tools).
Run code quality checks after implementation using MCP code-checker tools.
```

## Integration Points

**Imports needed in `issues.py`:**
```python
from typing import Any
from ...utils.github_operations.issues import IssueBranchManager, IssueData, IssueManager
from ...utils.user_config import get_cache_refresh_minutes, load_config
from .config import get_github_username, load_repo_vscodeclaude_config, load_vscodeclaude_config
from .helpers import get_issue_status, get_repo_full_name
```

**Imports to update in `commands.py`:**
```python
from ....workflows.vscodeclaude.issues import (
    build_eligible_issues_with_branch_check,  # NEW
    get_cached_eligible_vscodeclaude_issues,
    get_linked_branch_for_issue,
    status_requires_linked_branch,
)
```

## Acceptance Criteria

- [ ] `build_eligible_issues_with_branch_check()` function created in `issues.py`
- [ ] Function returns correct tuple of eligible issues and issues_without_branch set
- [ ] CLI command refactored to use new helper (code reduced from ~45 to ~10 lines)
- [ ] All tests pass including new test coverage for the helper
- [ ] Pylint, pytest, mypy all pass
- [ ] No behavioral changes - output identical to before refactoring

## Commit Message

```
refactor(vscodeclaude): extract eligible issues building to helper function

Extract build_eligible_issues_with_branch_check() from CLI command to
issues.py for better code reusability and separation of concerns.

- Add build_eligible_issues_with_branch_check() in issues.py
- Refactor execute_coordinator_vscodeclaude_status() to use helper
- Add comprehensive tests for new helper function
- Reduce CLI code from ~45 lines to ~10 lines

Part of issue #422: Status-aware branch handling

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
