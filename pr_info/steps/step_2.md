# Step 2: Remove `get_linked_branch_for_issue()` Wrapper, Update All Callers

> **Context**: Read `pr_info/steps/summary.md` for architectural overview of issue #264.
> **Prerequisite**: Step 1 must be complete (enhanced `get_branch_with_pr_fallback()`).

## Goal

Delete the `get_linked_branch_for_issue()` wrapper entirely. Update all 4 call sites and 1 export to call `branch_manager.get_branch_with_pr_fallback()` directly. Remove all `try/except ValueError` blocks. Fix the latent bug in `_handle_intervention_mode()`.

## Approach: TDD

Update tests first to expect the new call pattern, then modify the production code.

---

## Part A: Delete `get_linked_branch_for_issue()` and update `issues.py`

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/issues.py`
- `src/mcp_coder/workflows/vscodeclaude/__init__.py`

### WHAT

1. **Delete** the `get_linked_branch_for_issue()` function entirely from `issues.py`
2. **Remove** `get_linked_branch_for_issue` from the import in `__init__.py` and from `__all__`
3. **Update** `build_eligible_issues_with_branch_check()`:
   - Remove `try/except ValueError` block
   - Call `branch_manager.get_branch_with_pr_fallback(issue_number, repo_owner, repo_name)` directly
   - `repo_owner` and `repo_name` are already available: split `repo_full_name` on `"/"`

### ALGORITHM — updated `build_eligible_issues_with_branch_check` branch check
```python
# Old:
try:
    branch = get_linked_branch_for_issue(branch_manager, issue["number"])
    if branch is None:
        issues_without_branch.add(...)
except ValueError:
    issues_without_branch.add(...)

# New:
repo_owner, repo_name = repo_full_name.split("/", 1)
branch = branch_manager.get_branch_with_pr_fallback(
    issue["number"], repo_owner, repo_name
)
if branch is None:
    issues_without_branch.add(...)
```

### TESTS to update
- `tests/workflows/vscodeclaude/test_issues.py`:
  - Remove test for `get_linked_branch_for_issue` raising `ValueError`
  - Remove test for `get_linked_branch_for_issue` returning single/none
  - Update `build_eligible_issues_with_branch_check` tests to mock `get_branch_with_pr_fallback` instead of `get_linked_branch_for_issue`

---

## Part B: Update `session_launch.py` (`process_eligible_issues`)

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`

### WHAT

1. **Remove** import of `get_linked_branch_for_issue` from `.issues`
2. **Remove** `try/except ValueError` block around branch resolution
3. **Call** `branch_manager.get_branch_with_pr_fallback()` directly

### ALGORITHM — updated branch resolution in `process_eligible_issues`
```python
# Old:
try:
    branch_name = get_linked_branch_for_issue(branch_manager, issue["number"])
except ValueError:
    logger.error("Issue #%d at %s has multiple branches linked - skipping", ...)
    continue

# New (repo_full_name already available in this function):
repo_owner, repo_name_str = repo_full_name.split("/", 1)
branch_name = branch_manager.get_branch_with_pr_fallback(
    issue["number"], repo_owner, repo_name_str
)
# None already covers: no branch, multiple branches, ambiguous — all skip paths
```

The existing check `if status_requires_linked_branch(status) and branch_name is None` remains unchanged — it naturally handles all failure cases now.

### TESTS to update
- `tests/workflows/vscodeclaude/test_orchestrator_launch.py`:
  - Update mocks from `get_linked_branch_for_issue` to `get_branch_with_pr_fallback`
  - Remove `ValueError`-raising mock scenarios, replace with `return_value=None`

---

## Part C: Update `session_restart.py` (`_prepare_restart_branch`)

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`

### WHAT

1. **Remove** import of `get_linked_branch_for_issue` from `.issues`
2. **Remove** `try/except ValueError` block
3. **Call** `branch_manager.get_branch_with_pr_fallback()` directly
4. **Remove** `"Multi-branch"` skip reason — now covered by `"No branch"` (returns `None`)

### ALGORITHM — updated `_prepare_restart_branch`
```python
# Old:
try:
    linked_branch = get_linked_branch_for_issue(branch_manager, issue_number)
except ValueError:
    return BranchPrepResult(False, "Multi-branch", None)

# New (need repo_owner/repo_name — derive from branch_manager or add params):
# Option: add repo_owner, repo_name params to _prepare_restart_branch
linked_branch = branch_manager.get_branch_with_pr_fallback(
    issue_number, repo_owner, repo_name
)
# None return naturally flows to: if not linked_branch: return BranchPrepResult(False, "No branch", None)
```

### DATA — parameter change
`_prepare_restart_branch` needs `repo_owner` and `repo_name` added to its signature:
```python
def _prepare_restart_branch(
    folder_path: Path,
    current_status: str,
    branch_manager: IssueBranchManager,
    issue_number: int,
    repo_owner: str,     # NEW
    repo_name: str,      # NEW
) -> BranchPrepResult:
```

The caller in `restart_closed_sessions()` already has `repo_full_name` available from `session["repo"]` — just split it.

### TESTS to update
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`:
  - Update mocks from `get_linked_branch_for_issue` to `get_branch_with_pr_fallback`
  - Remove `ValueError`-raising mock for multi-branch, replace with `return_value=None`
  - Update `_prepare_restart_branch` calls in tests with new params

---

## Part D: Update `commands.py` (`_handle_intervention_mode`) — fixes latent bug

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT

1. **Remove** import of `get_linked_branch_for_issue` from `....workflows.vscodeclaude`
2. **Replace** bare call with `branch_manager.get_branch_with_pr_fallback()`
3. **Add** warning log when `branch_name is None` — this is the fix for the latent bug where `ValueError` was never caught

### ALGORITHM
```python
# Old (latent bug — ValueError not caught):
branch_name = get_linked_branch_for_issue(branch_manager, args.issue)

# New:
repo_full_name = _get_repo_full_name_from_url(repo_url)
repo_owner, repo_name_str = repo_full_name.split("/", 1)
branch_name = branch_manager.get_branch_with_pr_fallback(
    args.issue, repo_owner, repo_name_str
)
if branch_name is None:
    logger.warning(
        "Issue #%d: no single branch could be resolved (multiple linked, "
        "or no branch found) — using default branch",
        args.issue,
    )
```

### TESTS to update
- `tests/cli/commands/coordinator/test_commands.py`:
  - Update any mocks of `get_linked_branch_for_issue` to `get_branch_with_pr_fallback`

---

## LLM Prompt for Step 2

```
You are implementing Step 2 of issue #264 for the mcp-coder project.
Read pr_info/steps/summary.md for full context, then read this step file (pr_info/steps/step_2.md).
Step 1 is already complete — get_branch_with_pr_fallback() now handles all resolution including
multiple-linked-branches (returns None), closed PRs, and pattern search.

Your task: Remove the get_linked_branch_for_issue() wrapper and update all callers.

Read these files before making changes:
- src/mcp_coder/workflows/vscodeclaude/issues.py
- src/mcp_coder/workflows/vscodeclaude/__init__.py
- src/mcp_coder/workflows/vscodeclaude/session_launch.py
- src/mcp_coder/workflows/vscodeclaude/session_restart.py
- src/mcp_coder/cli/commands/coordinator/commands.py

And read these test files:
- tests/workflows/vscodeclaude/test_issues.py
- tests/workflows/vscodeclaude/test_orchestrator_launch.py
- tests/workflows/vscodeclaude/test_orchestrator_sessions.py
- tests/cli/commands/coordinator/test_commands.py

Follow TDD: update tests first to expect the new call pattern, then modify production code.
For each Part (A through D), update the tests, then the production code, then run tests.

Key constraints:
- Delete get_linked_branch_for_issue entirely — don't leave it as deprecated
- All callers derive repo_owner/repo_name by splitting repo_full_name on "/"
- No try/except ValueError anywhere — None handles all failure cases
- _handle_intervention_mode: add logger.warning when branch is None (fixes latent bug)
- _prepare_restart_branch: add repo_owner, repo_name parameters
- Remove "Multi-branch" skip reason from session_restart — "No branch" covers it
```
