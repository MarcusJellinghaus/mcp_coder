# Step 3: Update `branch_status.py` — multi-run log fetching (TDD)

> **Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE
- **Test:** `tests/checks/test_branch_status.py`
- **Source:** `src/mcp_coder/checks/branch_status.py`

## WHAT — Tests first

### Update existing `_build_ci_error_details` tests
Existing tests mock `ci_manager.get_run_logs(run_id)` with a single `run_id` from `status_result["run"]["id"]`.
Update test fixtures:
- Change `"run": {"id": 123, ...}` → `"run": {"run_ids": [123], ...}`
- Add `"run_id": 123` to each job dict in `"jobs"` list
- Existing assertions should still pass (single-run case unchanged)

### Add new multi-run log fetching tests
```python
def test_build_ci_error_details_fetches_logs_from_multiple_runs() -> None:
    """Logs should be fetched per distinct run_id among failed jobs (up to 3)."""
    # Setup: 2 runs, each with a failed job from different run_id
    # Assert: get_run_logs called twice (once per run_id)
    # Assert: output contains logs from both runs

def test_build_ci_error_details_caps_at_3_failed_runs() -> None:
    """Only fetch logs from first 3 distinct failed run_ids."""
    # Setup: 4 runs, each with a failed job
    # Assert: get_run_logs called exactly 3 times
    # Assert: 4th run's jobs listed by name only

def test_build_ci_error_details_multiple_runs_github_urls() -> None:
    """Each job section should link to its own run's URL."""
    # Setup: 2 runs with different IDs, run URL template
    # Assert: job URLs point to correct run_id
```

### Update `test_collect_ci_status_with_truncation`
The mock `get_latest_ci_status` return value needs `run_ids` instead of `id`:
- Change `"run": {"id": 123, ...}` → `"run": {"run_ids": [123], ...}`
- Add `"run_id": 123` to job dicts

## WHAT — Source changes

### Update `_collect_ci_status()` — minimal change
Currently reads `run_data = status_result["run"]` then `run_data.get("conclusion")`.
This works unchanged because `run["conclusion"]` is now the aggregate value.
**No code changes needed** in `_collect_ci_status()`.

### Update `_build_ci_error_details()` — multi-run log fetching
Currently fetches logs once: `ci_manager.get_run_logs(run_id)`.

**Algorithm (updated):**
```
# Collect distinct run_ids from failed jobs
failed_jobs = [j for j in jobs_data if j["conclusion"] == "failure"]
failed_run_ids = list(dict.fromkeys(j["run_id"] for j in failed_jobs))  # unique, ordered

# Fetch logs for up to 3 failed run_ids
all_logs: Dict[str, str] = {}
fetched_run_ids = failed_run_ids[:3]
for rid in fetched_run_ids:
    try:
        run_logs = ci_manager.get_run_logs(rid)
        all_logs.update(run_logs)
    except Exception as e:
        logger.warning(f"Failed to get logs for run {rid}: {e}")

# Use all_logs (merged) for the rest of the function (unchanged logic)
```

Also update the URL construction: each job's section should use its own `run_id` for the URL, not the single `run_data["id"]`. The `run_data.get("url")` gives the base URL pattern — for per-job URLs, construct from `run_data.get("url")` base or from the job's `run_id`.

**Specific change for job URL:** Replace `run_url` references with per-job URL construction:
```python
# For each job in the loop:
job_run_id = job.get("run_id")
# Base URL pattern: https://github.com/user/repo/actions/runs/{run_id}
# Use run_ids[0]'s URL as template, replace the run ID portion
```

Simpler approach: store first run's URL as before. For `View job:` links, use the job's own `run_id`:
```python
# Existing: f"{run_url}/job/{job_id}"
# If run_url is for run 123 but job belongs to run 456, 
# replace run ID in URL or just use: no change needed if URL is just for navigation hint
```

Actually, the simplest correct approach: since `run_url` is just used for display/navigation, keep using first run's URL for the top-level `GitHub Actions:` link. For per-job `View job:` links, construct from the repo URL base.

## HOW — Integration
- `_build_ci_error_details` already receives `ci_manager` and `status_result`
- Jobs now have `run_id` field (from step 2)
- `get_run_logs()` is called per distinct `run_id` instead of once

## DATA
No changes to return types. `_build_ci_error_details` still returns `Optional[str]`.

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 3 from pr_info/steps/step_3.md.

Update tests FIRST in tests/checks/test_branch_status.py:
- Update existing _build_ci_error_details test fixtures: "id" → "run_ids", add "run_id" to jobs
- Add tests for multi-run log fetching (2 runs, 4 runs capped at 3)

Then update _build_ci_error_details() in src/mcp_coder/checks/branch_status.py:
- Fetch logs per distinct run_id from failed jobs (up to 3)
- Merge all logs into one dict, then use existing per-job display logic
Run tests to verify all pass.
```
