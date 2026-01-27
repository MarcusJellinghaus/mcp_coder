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
