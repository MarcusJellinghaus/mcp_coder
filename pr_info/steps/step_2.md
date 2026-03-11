# Step 2: Rewrite `get_latest_ci_status()` for multi-workflow support (TDD)

> **Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE
- **Test:** `tests/utils/github_operations/test_ci_results_manager_status.py`
- **Source:** `src/mcp_coder/utils/github_operations/ci_results_manager.py`

## WHAT — Tests first

### Update existing `TestGetLatestCIStatus` tests
All existing tests mock `repo.get_workflow_runs.return_value = [mock_run]` with a single run.
These should continue to pass with minimal changes:
- Assertions on `result["run"]["id"]` → change to `result["run"]["run_ids"]` containing the ID
- Add assertion that `result["jobs"][n]["run_id"]` equals the mock run's ID

### Add new multi-workflow test class `TestGetLatestCIStatusMultiWorkflow`
```python
def test_two_workflows_one_fails_one_passes(self, mock_repo, ci_manager) -> None:
    """Aggregate conclusion should be 'failure'."""

def test_two_workflows_one_pending_one_passes(self, mock_repo, ci_manager) -> None:
    """Aggregate status should be 'in_progress', conclusion None."""

def test_two_workflows_both_pass(self, mock_repo, ci_manager) -> None:
    """Aggregate conclusion should be 'success'."""

def test_mixed_head_sha_only_latest_counted(self, mock_repo, ci_manager) -> None:
    """Runs with different head_sha should be excluded."""

def test_jobs_merged_across_workflows(self, mock_repo, ci_manager) -> None:
    """Jobs from both runs should appear in result['jobs']."""

def test_jobs_carry_run_id(self, mock_repo, ci_manager) -> None:
    """Each job's run_id should match its parent workflow run."""

def test_jobs_call_failure_aborts_entirely(self, mock_repo, ci_manager) -> None:
    """If .jobs() raises on any run, decorator returns empty default."""
```

Each test sets up multiple mock runs with the same `head_sha`, each returning different jobs from `.jobs()`.

## WHAT — Source changes

Rewrite `get_latest_ci_status()` body (keep signature, decorator, validation):

**Algorithm:**
```
runs_paged = repo.get_workflow_runs(branch=branch)
try: first_run = runs_paged[0]
except IndexError: return empty

# Filter to latest commit SHA (uses pure function from step 1)
all_runs = list(runs_paged[:25])  # cap iteration
same_sha_runs = filter_runs_by_head_sha(all_runs)

# Aggregate conclusion across all runs
agg_conclusion, agg_status = aggregate_conclusion(same_sha_runs)

# Fetch and merge jobs from all runs (inline, ~5 lines)
all_jobs = []
for run in same_sha_runs:
    for job in run.jobs():
        all_jobs.append(JobData with run_id=run.id, ...)

# Build aggregate run_data dict
run_data = {
    "run_ids": [r.id for r in same_sha_runs],
    "status": agg_status,
    "conclusion": agg_conclusion,
    "workflow_name": first_run.name,  # first run's name for display
    "commit_sha": first_run.head_sha,
    ... other fields from first_run ...
}

return CIStatusData(run=run_data, jobs=all_jobs)
```

**Key detail:** The `run` dict no longer has `"id"` (int). It has `"run_ids"` (List[int]). The `"url"` field uses the first run's URL. `"workflow_name"` uses the first run's name (display-only).

## HOW — Integration
- Uses `filter_runs_by_head_sha()` and `aggregate_conclusion()` from step 1
- `@_handle_github_errors` decorator catches any `.jobs()` failure → returns empty default
- No changes to decorator or method signature

## DATA — Return values
`CIStatusData` structure (unchanged TypedDict, but `run` dict contents change):
```python
{
    "run": {
        "run_ids": [123, 456],        # NEW (was "id": 123)
        "status": "completed",         # aggregated
        "conclusion": "failure",       # aggregated
        "workflow_name": "CI",         # from first run
        "event": "push",
        "workflow_path": ".github/workflows/ci.yml",
        "branch": "feature/xyz",
        "commit_sha": "abc123",
        "created_at": "2024-01-15T10:30:00Z",
        "url": "https://github.com/.../runs/123"
    },
    "jobs": [
        {"id": 1, "run_id": 123, "name": "test", ...},
        {"id": 2, "run_id": 456, "name": "lint", ...}
    ]
}
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 2 from pr_info/steps/step_2.md.

Write/update tests FIRST in tests/utils/github_operations/test_ci_results_manager_status.py,
then rewrite get_latest_ci_status() in src/mcp_coder/utils/github_operations/ci_results_manager.py.

Update existing tests: change run["id"] assertions to run["run_ids"], add run_id assertions on jobs.
Add TestGetLatestCIStatusMultiWorkflow class with multi-run scenarios.
Then rewrite the method to filter by head_sha, aggregate conclusions, merge jobs.
Run tests to verify all pass.
```
