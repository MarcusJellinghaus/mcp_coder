# Decisions — Issue #511

## Decision 1: Keep `filter_runs_by_head_sha`
**Context:** Function filters runs to latest commit SHA. PyGithub already sorts by `created_at` desc, so runs from the same push share the same SHA naturally.
**Decision:** Keep as a defensive pure function. Low cost, adds safety against race conditions during rapid pushes.

## Decision 2: Simplify URL construction in Step 3
**Context:** Plan proposed complex per-job URL rewriting when jobs come from different workflow runs.
**Decision:** Keep existing URL pattern (`f"{run_url}/job/{job_id}"`). GitHub job IDs are globally unique within a repo — the URL resolves correctly regardless of which run URL prefixes it. Remove URL complexity from step 3.

## Decision 3: Log fetching uses failed jobs' run_ids
**Context:** `_run_ci_analysis_and_fix()` in `core.py` originally planned to use `run_ids[0]` for log fetching, which could pick a passing run.
**Decision:** Extract distinct `run_id` values from failed jobs and fetch logs from those. Same pattern as step 3's `_build_ci_error_details`.

## Decision 4: Add `RunData` TypedDict
**Context:** The `run` dict in `CIStatusData` is typed as `Dict[str, Any]`. We're changing its shape (removing `"id"`, adding `"run_ids"`).
**Decision:** Add a `RunData` TypedDict for stronger type safety. Goes into step 1 alongside the `JobData` update.

## Decision 5: Keep Step 5 separate
**Context:** Step 5 is purely validation (run all tests, grep for leftover references). Could be merged into step 4.
**Decision:** Keep as a separate explicit validation step to act as a safety net.

## Decision 6: Add `"timed_out"` to failure conditions
**Context:** GitHub Actions runs can have `conclusion: "timed_out"` in addition to `"failure"` and `"cancelled"`.
**Decision:** Add `"timed_out"` alongside `"failure"` and `"cancelled"` in `aggregate_conclusion`.

## Decision 7: Partial results on `.jobs()` failure
**Context:** If `.jobs()` fails for one run in a multi-run fetch, aborting entirely loses data from successful runs.
**Decision:** Try/except per-run `.jobs()` call. Log warning, skip that run's jobs, return partial results. Downstream display should prepend a visible warning that some jobs could not be fetched and need manual inspection.

## Decision 8: Use `SimpleNamespace` for pure function tests
**Context:** `filter_runs_by_head_sha` and `aggregate_conclusion` access attributes (`.head_sha`, `.conclusion`, `.status`) via dot notation. Plain dicts don't support attribute access.
**Decision:** Use `types.SimpleNamespace` in tests. Lightweight stdlib option that supports dot access without the overhead of `MagicMock`.

## Decision 9: Add `jobs_fetch_warning` to `RunData` TypedDict
**Context:** Step 2 adds a `jobs_fetch_warning` key to the run dict when `.jobs()` fails (Decision 7), but the `RunData` TypedDict from Step 1 didn't include it, which would cause mypy errors.
**Decision:** Add `jobs_fetch_warning: NotRequired[str]` to `RunData` in Step 1.
