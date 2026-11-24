# Step 7 — Documentation

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, then implement Step 7 only (docs; no code
> changes). Check each statement against the code from Steps 1–6 (`commands.py`, `core.py`,
> `client.py`, `user_config.py`). Follow the "Writing style" rules in `.claude/CLAUDE.md`. Run
> the fast unit tests (some tests check docs), run the formatter, and make exactly one commit:
> `docs(coordinator): document capacity gate, dispatch delay and global order`.

## WHERE / WHAT

### `docs/repository-setup/jenkins.md`

1. **"The Coordinator Is Fail-Fast"**:
   - "remaining issues in that repository are not attempted, and under `--all` neither are the
     remaining repositories" → issues are collected from all repos first and dispatched from one
     global list; the first failure ends the run, remaining issues (any repo) are not attempted.
     A rate limit or config error in a later repo now ends the run before any dispatch.
   - "a single coordinator error line — `Failed processing issue #N`" → also the lookup line
     (`Failed to look up job '<path>': ...`) and the gate line (`Failed to list builds under
     '<path>': ...`), both exit 1. The lookup line has no traceback above it; the gate line may
     have the `get_recent_builds ... FAILED` traceback above it, like `start_job`.
2. **"Troubleshooting"**: the examples quote `Failed to start job …`. A wrong path, missing
   Job/Read or missing Overall/Read now fail first in the job lookup → change those examples to
   `Failed to look up job 'Windows-Agents/Executor': ...`. Missing Job/Build still fails at
   `start_job` (keep that wording where the text talks about Job/Build). Add a short entry:
   "`... is not a job`" → `executor_job_path` names a folder.
3. **New section "Executor Capacity Gate"** (after the fail-fast section), covering:
   - Before every dispatch the coordinator lists the executor job's running builds; a build still
     named `#<number>` is waiting for an agent → that job is blocked for the rest of the run, its
     issues are skipped, other executor jobs continue in global order. Repos whose job is busy at
     run start are not fetched from GitHub at all (also with `--force-refresh`).
   - **Dependency on the Executor pipeline:** the top-level `agent { label 'windows-agent' }` in
     the Executor job's inline pipeline script (AutoRunner `jenkins-windows/README.md`, Step 4
     item 7; not version-controlled), and `mcpCoderExecutorWindows.groovy` setting
     `currentBuild.displayName` from `LABEL` at its start. If the name is ever set before agent
     allocation (e.g. in a controller-side stage), the gate silently stops blocking.
   - Why the build list and not the queue: after the quiet period the build runs on the
     controller (library checkout) and waits for the agent as a `PlaceholderTask` that does not
     reliably carry the job URL.
   - **Delay vs. quiet period:** `dispatch_delay_seconds` (default 15) must exceed the Jenkins
     quiet period (5 s default), else the re-check misses the build just started and dispatches
     again. A re-check that comes before the new build got its agent only blocks the job until
     the next run (harmless). `buildWithParameters?delay=` is not used (a delayed build sits in
     the queue, invisible to the gate).
   - **Manual Executor builds without `LABEL`** keep `#<number>`: they block the coordinator
     until they finish and, after 60 min, log a WARNING on every run (→ UNSTABLE coordinator
     build). Accepted: they use an executor.
   - **The coordinator holds an agent executor itself** (it runs on `windows-agent`) and its
     `venvLockResource` slot, both also while it sleeps; the waiting build usually gets that
     executor once the coordinator run ends.
   - **Run length:** each started build adds one delay before the next dispatch, so a run with a
     few starts exceeds 60 s and the next coordinator build (`disableConcurrentBuilds()`) starts
     right after it. There is no sleep after the last dispatch; the next run sees that build only
     because its own startup (library checkout, agent allocation, Python startup) takes longer
     than the quiet period.
   - **Per-job scope:** blocking is per executor job while capacity is per agent label. Correct
     while the configured repos share one executor job; two executor jobs on the same agent label
     would compete first-in, first-out again.
   - Dispatch order: one list across all repos, 81 → 71 → 08 → 17 → 05 → 14 → 02, ties by
     config repo order.

### `docs/repository-setup/github.md` (line ~428, "Cost")

Replace "every coordinator run repeats one lookup and one summary entry per such issue" with:
the trust lookup runs only for issues reached while their executor job is free (repos of a busy
job are not fetched), so an untrusted issue costs at most one lookup and one summary entry per
run.

### `docs/cli-reference.md` (`### coordinator`)

Add bullets: issues of all repositories are dispatched from one list in reverse pipeline order;
a build starts only while the executor job has no build waiting for an agent, with
`dispatch_delay_seconds` between starts (link Jenkins Setup → "Executor Capacity Gate" and the
Configuration Guide). Exit 1 for a wrong `executor_job_path`.

### `docs/configuration/config.md` (`### [coordinator]`)

Add a table row: `dispatch_delay_seconds` | integer | Seconds to wait after starting a build,
before the next dispatch; must exceed the Jenkins quiet period (5 s default) | No | 15. Add one
line: a non-integer is a config error (exit 1); ≤ 0 → warning, 15 is used. Add it to the
default-configuration example.

### `docs/architecture/architecture.md` (line ~129)

"It finds issues in a trigger label and starts the executor job once per issue" → collects the
issues of all repos in one list (reverse pipeline order) and starts the executor job once per
issue while the job has capacity (no build waiting for an agent), with a delay between starts.

### Code docstrings

Verify (fix if Step 4 missed it) that the `get_eligible_issues` docstring no longer lists
08 → 05 → 02 or claims a sort.

## Tests

None new. Run the fast unit tests to make sure no docs-checking test breaks.
