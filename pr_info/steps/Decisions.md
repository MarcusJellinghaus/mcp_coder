# Implementation Decisions

This document logs the decisions made during the plan review discussion.

## Testing Strategy
**Decision**: Add key integration tests that test the complete workflow end-to-end (Option B)
**Rationale**: Will help catch issues with the complete workflow while maintaining good unit test coverage.

## Setup Command Validation
**Decision**: Add pre-validation to check if commands exist in PATH before attempting to run them (Option B)
**Rationale**: Prevents cryptic error messages when tools like `uv` aren't installed. Will check command availability before running setup commands.

## Progress Feedback
**Decision**: Add basic progress messages using `log.info()` for operations like "Cloning repository..." and "Running setup commands..." (Option B)
**Rationale**: Provides user feedback during long operations while keeping implementation simple and consistent with existing logging approach.

## Session Recovery
**Decision**: Add cleanup logic to remove the working folder if session creation fails after folder creation (Option B)
**Rationale**: Prevents accumulation of broken/partial folders when session creation fails partway through.

## Workspace File Location
**Decision**: Keep workspace files in `workspace_base` as planned (Option A)
**Rationale**: Simple approach where files get naturally managed - either overwritten on reuse or cleaned up when folders are deleted.

## Intervention Mode Scope
**Decision**: Only work with specific issue numbers as planned - requires `--issue NUMBER` (Option A)
**Rationale**: Keeps intervention mode focused and controlled.

## Platform Coverage
**Decision**: Support only Windows and Linux as planned (Option A)
**Rationale**: Focuses scope on the main platforms while keeping implementation manageable.

## Git Branch Handling
**Decision**: Keep the current approach - error on multiple branches linked to an issue (Option A)
**Rationale**: Encourages clean branch management practices.

## Session Restart Behavior
**Decision**: Launch VSCode immediately for restarted sessions, same as new sessions (Option A)
**Rationale**: Maintains seamless workflow experience.

## Implementation Approach
**Decision**: All decisions above will be incorporated into the implementation steps.

---

## Code Review Decisions (Step 9)

### IssueManager Instantiation Fix
**Decision**: Fix the incorrect IssueManager/IssueBranchManager instantiation (Option A - implement fix)
**Rationale**: Critical bug - passing `repo_full_name` ("owner/repo") as positional argument is interpreted as `project_dir` (Path), not `repo_url`. Must use keyword argument with full GitHub URL.

### Duplicated Cleanup Logic
**Decision**: Remove duplicate `_cleanup_stale_sessions()` in commands.py and use the vscodeclaude.py version (Option A)
**Rationale**: The vscodeclaude.py implementation is more complete (checks dirty status, has dry_run support). Consolidating reduces maintenance burden.

### Mypy Module Override
**Decision**: Replace module-wide mypy override with specific `# type: ignore[unreachable]` comments (Option C)
**Rationale**: More precise suppression - only ignores the specific platform-check lines that cause false positives, rather than suppressing all unreachable warnings in the entire module.

### Magic Numbers in Display
**Decision**: Leave column width numbers as local variables (Option B)
**Rationale**: They are local to one function and easy to understand. Extracting to constants would add complexity without significant benefit.

### Logger f-strings
**Decision**: Leave f-strings in logger calls as-is (Option B)
**Rationale**: f-strings work fine and the performance difference is negligible for this use case. Minor style preference not worth changing.

---

## Code Review Decisions (Step 10)

### Race Condition in Session Files
**Decision**: Add documentation warning (Option B)
**Rationale**: This is a manual command run once at a time. Adding file locking (requires new dependency) is overkill for the expected usage pattern.

### Invalid repo_url Reconstruction
**Decision**: Fail fast with ValueError (Option A)
**Rationale**: When `_get_repo_full_name()` returns "unknown/repo", raise an error immediately so the user knows their config is wrong, rather than letting GitHub API calls fail with confusing errors.

### Missing Stale Check in restart_closed_sessions
**Decision**: Add `is_session_stale()` check (Option A)
**Rationale**: Don't restart sessions where the issue status has changed. This avoids restarting sessions that would immediately be flagged for cleanup.

### Double import json in Test File
**Decision**: Remove redundant import (Option A)
**Rationale**: The import at line 306 inside a test method is redundant since json is already imported at the top of the file.

### Unused issue_manager Parameter
**Decision**: Remove the parameter (Option A)
**Rationale**: `handle_pr_created_issues` has an unused `issue_manager` parameter marked as "kept for API compatibility", but this is a new function with no existing callers.

### Mixed Type Hint Styles
**Decision**: Standardize to modern syntax (Option A)
**Rationale**: Convert all type hints to Python 3.9+ syntax (`list`, `dict`, `set` instead of `List`, `Dict`, `Set`) since the project requires Python 3.11+.

### Empty Placeholder Tests
**Decision**: Remove the TestIntegration class (Option A)
**Rationale**: Empty placeholder tests with just `pass` can cause confusion about actual test coverage. Remove them rather than keeping as reminders.

---

## Performance Optimization Decisions (Step 12)

### Issue Cache Strategy
**Decision**: Use the existing `get_all_cached_issues()` function from `issue_cache.py` (Option A - shared cache)
**Rationale**: The cache already exists and works well for `coordinator run`. Both commands should use the SAME cache file and the SAME cache functions, just with different filtering logic applied afterward. No new cache infrastructure needed.

### Issue Data Flow
**Decision**: Pass cached issues dict through to functions instead of re-fetching (Option A - look up from cache)
**Rationale**: Once `get_all_cached_issues()` is called, that data should be passed to all functions that need issue data. Functions like `is_session_stale()` and `restart_closed_sessions()` should look up issues from the passed cache dict instead of making individual `get_issue()` API calls.

### Filter Function Location
**Decision**: Add `_filter_eligible_vscodeclaude_issues()` helper in `issues.py` (analogous to `_filter_eligible_issues()` in `core.py`)
**Rationale**: Keeps filtering logic separate from cache logic. The cache returns ALL issues, filtering is applied by the caller.
