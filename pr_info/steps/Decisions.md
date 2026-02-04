# Decisions Log for Issue #400

## Discussed Decisions

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Dry-run cleanup behavior | Keep current behavior - only run cleanup when `--cleanup` is passed | Cleaner output; avoid noisy dry-run messages when user didn't ask for cleanup |
| 2 | Shared helper for cached issues | Modify existing `_build_cached_issues_by_repo()` to return `tuple[dict, set[str]]` | Function already exists; add `failed_repos` to return value for `(?)` indicator |
| 3 | Race condition / file locking | Not needed for `update_session_status()` | Only one vscodeclaude process runs at a time in practice |
| 4 | Issue not in cache handling | Current caching is sufficient | If issue missing from cache after successful API call, it's closed/deleted - session is stale |
| 5 | Module `__all__` exports | Skip adding `__all__` to `issues.py` | Keep consistent with current module style |
| 6 | Duplicate `get_issue_status()` | Remove `_get_issue_status()` from status.py, use `get_issue_status()` from helpers.py | Avoid duplication; helpers.py is the designated place for shared utilities |
| 7 | Manual intervention messages | Use plain text without emojis: `"!! Manual cleanup"` and `"!! Manual (label-name)"` | Consistent formatting across Next Action column |
| 8 | Blocked + stale priority | Add test confirming blocked takes priority over stale | When unblocked, session becomes "just stale" and can be cleaned up then |
| 9 | `(?)` indicator position | Show after status: `04:plan-review (?)` | More natural reading order |
| 10 | Dry-run message improvement | Change to `Add --cleanup to delete: XYZ`, skip dirty folders | Actionable message; dirty folders can't be auto-cleaned anyway |
