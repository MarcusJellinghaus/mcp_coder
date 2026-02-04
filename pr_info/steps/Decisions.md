# Decisions Log for Issue #400

## Discussed Decisions

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Dry-run cleanup behavior | Keep current behavior - only run cleanup when `--cleanup` is passed | Cleaner output; avoid noisy dry-run messages when user didn't ask for cleanup |
| 2 | Shared helper for cached issues | Extract `_build_cached_issues_by_repo()` helper function | Avoid code duplication between `execute_coordinator_vscodeclaude()` and `execute_coordinator_vscodeclaude_status()` |
| 3 | Race condition / file locking | Not needed for `update_session_status()` | Only one vscodeclaude process runs at a time in practice |
| 4 | Issue not in cache handling | Current caching is sufficient | If issue missing from cache after successful API call, it's closed/deleted - session is stale |
| 5 | Module `__all__` exports | Skip adding `__all__` to `issues.py` | Keep consistent with current module style |
