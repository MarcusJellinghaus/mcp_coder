# Decisions Log for Issue #422

Decisions made during plan review discussion.

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Git fetch failure handling | **Fatal for all statuses** - any fetch failure returns `(False, "Git error", None)` and skips restart | If network is down, continuing could cause confusing errors on subsequent git operations |
| 2 | `_prepare_restart_branch()` return type | **Use NamedTuple** - `BranchPrepResult` with named fields `should_proceed`, `skip_reason`, `branch_name` | More Pythonic, self-documenting, prevents ordering bugs with two `str \| None` values |
| 3 | Multiple linked branches | **Treat as skip reason** - catch `ValueError`, return `skip_reason="Multi-branch"`, show `!! Multi-branch` in status table | User needs clear feedback when issue has multiple branches linked |
| 4 | Branch manager instantiation | **Keep as-is** - no caching optimization needed | Manager instantiation is cheap; API call reduction already achieved by only calling `get_linked_branch_for_issue()` for status-04/07 |
| 5 | Step 6 algorithm fix | **Add `status_requires_linked_branch()` check** before showing `→ Needs branch` | Without this, status-01 issues without branch would incorrectly show `→ Needs branch` |
| 6 | CLI caller code location | **Refactor CLI to use `display_status_table()`** - update `execute_coordinator_vscodeclaude_status()` in `commands.py` to call `display_status_table()` | Better separation of concerns; display logic belongs in `status.py` |

---

## Code Review Decisions (Post-Implementation)

Decisions made during code review discussion.

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 7 | CLI code duplication | **Extract to helper function** - Create `build_eligible_issues_with_branch_check()` in `issues.py` to encapsulate eligible issues building with branch checking logic | Reduces duplication, improves reusability, better separation of concerns |
| 8 | Multiple branches error messaging | **Keep current behavior** - `!! Multi-branch` indicator is clear enough | Users can understand the issue without additional guidance |
| 9 | Git operation error specificity | **Keep generic "Git error"** - Single error message covers fetch/checkout/pull failures | Simplicity outweighs debugging benefit; generic message is adequate |
| 10 | Branch checkout documentation | **Leave docstring as-is** - "checkout if different" describes logical intent | Git checkout is idempotent; explicit check not needed in code |
| 11 | Status file redundant write | **Remove redundant write** - Delete conditional `create_status_file()` call after `regenerate_session_files()` in `restart_closed_sessions()` | Checkout happens before regenerate, so branch is already correct; double-write is unnecessary |
| 12 | Comprehensive documentation | **Add decision matrix to module docstring** - Create comprehensive decision matrix, common scenarios, and state transitions in orchestrator.py docstring | Complex business logic needs single definitive reference showing all state combinations and outcomes |
