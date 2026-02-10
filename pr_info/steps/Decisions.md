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
