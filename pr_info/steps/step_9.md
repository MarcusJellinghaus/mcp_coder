# Step 9: Code Review Fixes

## Context
See `pr_info/steps/summary.md` for overall feature context.

This step addresses issues identified during code review of the vscodeclaude feature.

## Prerequisites
- Steps 1-8 completed
- All existing tests passing

## Objective
Fix critical bugs and improvements identified in code review:
1. Fix incorrect IssueManager/IssueBranchManager instantiation (critical bug)
2. Remove duplicated cleanup logic in commands.py
3. Replace module-wide mypy override with specific type ignore comments

---

## Task 9.1: Fix IssueManager/IssueBranchManager Instantiation

### WHERE
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Fix lines 1360-1361 and 1576 where `IssueManager` and `IssueBranchManager` are instantiated with incorrect arguments.

**Current (broken):**
```python
issue_manager: IssueManager = coordinator.IssueManager(repo_full_name)
branch_manager: IssueBranchManager = coordinator.IssueBranchManager(repo_full_name)
```

**Fixed:**
```python
repo_url = f"https://github.com/{repo_full_name}"
issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
branch_manager: IssueBranchManager = coordinator.IssueBranchManager(repo_url=repo_url)
```

### ALGORITHM
```
1. In process_eligible_issues(): Build repo_url from repo_full_name
2. Pass repo_url as keyword argument to IssueManager
3. Pass repo_url as keyword argument to IssueBranchManager
4. In is_session_stale(): Same fix for IssueManager instantiation
```

### Test Updates
Add test to verify correct repo_url is passed:
```python
def test_process_eligible_issues_uses_repo_url(self, monkeypatch):
    """Verify IssueManager is called with repo_url keyword argument."""
    # Mock coordinator and capture the call arguments
    # Assert repo_url is passed, not positional project_dir
```

---

## Task 9.2: Remove Duplicated Cleanup Logic

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Remove `_cleanup_stale_sessions()` function from `commands.py` (lines 567-599) and use the existing `cleanup_stale_sessions()` from `vscodeclaude.py` instead.

**Current:**
- `commands.py` has `_cleanup_stale_sessions(dry_run)` - simpler implementation
- `vscodeclaude.py` has `cleanup_stale_sessions(dry_run)` - complete implementation with dirty check

**Fixed:**
- Delete `_cleanup_stale_sessions()` from `commands.py`
- Import and use `cleanup_stale_sessions` from vscodeclaude module
- Update `execute_coordinator_vscodeclaude()` to call `cleanup_stale_sessions()`

### ALGORITHM
```
1. Add cleanup_stale_sessions to imports from vscodeclaude in commands.py
2. Delete _cleanup_stale_sessions function from commands.py
3. In execute_coordinator_vscodeclaude():
   - Replace _cleanup_stale_sessions(dry_run=False) with cleanup_stale_sessions(dry_run=False)
   - Replace _cleanup_stale_sessions(dry_run=True) with cleanup_stale_sessions(dry_run=True)
4. Update __init__.py to export cleanup_stale_sessions if not already exported
```

### HOW
Update imports in `commands.py`:
```python
from .vscodeclaude import (
    # ... existing imports ...
    cleanup_stale_sessions,  # Add this
)
```

---

## Task 9.3: Replace Module-Wide Mypy Override

### WHERE
- `pyproject.toml`
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`

### WHAT
Remove the module-wide mypy override and add specific `# type: ignore[unreachable]` comments on the lines that trigger false positives.

**Current in pyproject.toml:**
```toml
[[tool.mypy.overrides]]
module = ["mcp_coder.cli.commands.coordinator.vscodeclaude"]
disable_error_code = ["unreachable"]
```

### ALGORITHM
```
1. Run mypy without the override to identify exact lines with unreachable warnings
2. Add # type: ignore[unreachable] to those specific lines
3. Remove the [[tool.mypy.overrides]] section from pyproject.toml
4. Verify mypy passes
```

### Expected Lines (platform-specific code paths)
Lines in `create_startup_script()` where `is_windows` branches have unreachable code warnings due to mypy analyzing on a single platform.

---

## Verification

### Tests to Run
```bash
# Run all vscodeclaude tests
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-k", "test_vscodeclaude"])

# Run full quality checks
mcp__code-checker__run_all_checks()
```

### Success Criteria
- [ ] All existing tests still pass
- [ ] New test for repo_url verification passes
- [ ] No duplicate cleanup function in commands.py
- [ ] Mypy passes without module-wide override
- [ ] Pylint passes

---

## LLM Prompt

```
You are implementing Step 9 of the vscodeclaude feature.

Context: Read pr_info/steps/summary.md for overall context and pr_info/steps/step_9.md for this step's details.

Tasks:
1. Fix IssueManager/IssueBranchManager instantiation in vscodeclaude.py (lines 1360-1361, 1576)
   - Change from positional argument to repo_url keyword argument
   - Build URL as f"https://github.com/{repo_full_name}"

2. Remove _cleanup_stale_sessions() from commands.py and use cleanup_stale_sessions from vscodeclaude.py

3. Remove mypy override from pyproject.toml and add specific # type: ignore[unreachable] comments

After each change, run the code quality checks to verify.
```
