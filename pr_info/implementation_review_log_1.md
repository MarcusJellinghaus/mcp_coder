# Implementation Review Log 1

Branch: `feat/jenkins-executor-build-logs` (no linked issue)

Scope: Jenkins build tools — display name on `BuildInfo`, `--name-pattern`,
`--job` / `--all-jobs` with default from `executor_job_path` in the user config,
label-based log filenames with collision fallback, `index.csv`.

## Round 1 — 2026-10-28
**Findings**:
1. `--name-pattern` filtered only the `limit` builds fetched per job, so on a single job `--limit N` could return fewer than N matching builds (critical).
2. `get_recent_builds(folder=...)` now also takes job paths; parameter name and error text ("in folder") misleading.
3. Display names differing only in case collide on case-insensitive filesystems.
4. `index.csv` not written when a download fails part-way.

**Decisions**:
1. Accept — defeats the agreed "limit counts matching builds" behaviour.
2. Accept — bounded rename, error message was wrong for the default target.
3. Skip — speculative; real labels end in a unique `#<number>`.
4. Skip — acceptable failure mode for a developer tool.

**Changes**: with a name pattern, fetch `max(limit, BUILDS_CAP)` builds per job (new query-size test); renamed `folder` → `path` in `JenkinsClient.get_recent_builds`, error text "Failed to list builds under '<path>'", updated tool callers, unit and integration tests.

**Status**: committed

## Round 2 — 2026-10-28
**Findings**:
1. The job-path tree query is only unit-tested against hand-built dicts; integration tests still list a folder or the whole server.
2. `.scratch/` holds downloaded console logs; CI blocks PRs carrying it.
3. Pre-existing: `jenkins_integration` test `test_started_build_appears_with_console_output` fails in `get_job_status` (`client.py:414` strips `base_url` from the build URL; Jenkins returned `http://localhost:8080/...`, which differs from the configured URL).

**Decisions**:
1. Accept — exercise the new feature against real Jenkins.
2. Defer — untracked, still needed for the failure analysis; delete before opening the PR.
3. Skip — pre-existing, code untouched by this branch; reported to the user.

**Changes**: integration test lists `path=test_job` directly; new `test_job_path_lists_that_jobs_builds` (passes against real Jenkins).

**Status**: committed

## Round 3 — 2026-10-28
**Findings**: none.
**Decisions**: —
**Changes**: none.
**Status**: no changes needed

## Final Status

- 3 review rounds; 2 produced code changes (`0261623c`, `2f7ec351`), round 3 clean.
- vulture: clean. lint-imports: 19 contracts kept, 0 broken.
- Open, out of scope: pre-existing `get_job_status` integration failure (`client.py:414`, base-URL stripping) — candidate for a separate issue.
- Before the PR: delete `.scratch/` (console logs kept for the failure analysis).
