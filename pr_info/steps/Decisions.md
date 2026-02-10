# Decisions Log for Issue #340

Decisions made during plan review discussion.

---

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Implementing timeout | 120 minutes | As specified in the plan (changed from previous 60 minutes) |
| 2 | Staleness in dry-run | Run checks to show complete validation report | Users should see stale warnings even in preview mode |
| 3 | Missing timeout handling | Skip staleness check with warning | Alert user about missing config without failing |
| 4 | Steps 5 & 6 structure | Keep separate | Smaller incremental changes easier to review |
| 5 | Code reuse for issue-stats | Move existing functions from `workflows/issue_stats.py` | Reuse tested code, reduce implementation effort |
