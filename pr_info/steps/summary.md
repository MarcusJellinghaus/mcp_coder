# Issue #511: Fix multi-workflow CI status aggregation

## Problem
`get_latest_ci_status()` picks only `runs[0]` (one workflow run), so when multiple workflows trigger on the same commit, it may pick the passing one and miss a failing one.

## Design Changes

### Architectural Approach: Aggregate Inside `get_latest_ci_status()`

Instead of exposing a `runs` list to all consumers (breaking change), we keep `CIStatusData["run"]` as a single aggregate dict. The method internally fetches all runs for the latest commit's SHA, aggregates their conclusion, and merges all jobs.

**Key change to `run` dict:**
- Remove: `"id"` (single int)
- Add: `"run_ids"` (List[int]) — all workflow run IDs for the latest commit
- `"conclusion"` and `"status"` become **aggregated** values across all runs

This minimises consumer-side changes: code reading `run["conclusion"]` or `run["status"]` works unchanged. Only code comparing `run["id"]` (polling logic) needs updating to use `run["run_ids"]`.

### New `run_id` field on `JobData`
Each job carries `run_id: int` so consumers can trace which workflow run a job belongs to. Required for per-run log fetching.

### Two new pure functions (testable, no side effects)
1. `filter_runs_by_head_sha(runs, max_runs=25)` — filters to latest SHA only
2. `aggregate_conclusion(runs)` — failure > pending > success priority

### Aggregation rules

| Scenario | Aggregate conclusion |
|----------|---------------------|
| Any run `conclusion == "failure"` | `"failure"` |
| No failures, any run in_progress/queued/pending | `None` (with status `"in_progress"`) |
| All runs `conclusion == "success"` | `"success"` |
| No runs found | empty dict (existing behaviour) |

### Multi-run log fetching
`_build_ci_error_details()` fetches logs from up to 3 distinct failed `run_id`s (not just one), distributing the line budget across them.

### Polling logic
Run ID comparison in `core.py` and `check_branch_status.py` changes from single `id` comparison to set comparison on `run_ids`.

## Files Modified

### Source files (4):
| File | Changes |
|------|---------|
| `src/mcp_coder/utils/github_operations/ci_results_manager.py` | Add `run_id` to `JobData`, add 2 pure functions, rewrite `get_latest_ci_status()` |
| `src/mcp_coder/checks/branch_status.py` | `_build_ci_error_details()` fetches logs per distinct `run_id` (up to 3 runs) |
| `src/mcp_coder/workflows/implement/core.py` | Polling: compare `set(run_ids)` instead of single `id` |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Polling: compare `set(run_ids)` instead of single `id` |

### Test files (2):
| File | Changes |
|------|---------|
| `tests/utils/github_operations/test_ci_results_manager_status.py` | Update fixtures for `run_ids`/`run_id`, add tests for pure functions and multi-workflow scenarios |
| `tests/checks/test_branch_status.py` | Update `_build_ci_error_details` tests for multi-run log fetching |

### No new files created.
