# Step 2 — Thread `current_count` into `process_eligible_issues`

## Goal
Eliminate the per-repo `get_active_session_count()` call inside `process_eligible_issues`. Capacity tracking moves to the caller (`commands.py`), which threads `current_count` across the per-repo loop and updates the final summary log. As a Boy Scout cleanup in the same commit, drop the dead local `current_count += 1` increment inside the inner launch loop (it is unreachable bookkeeping after the `available_slots` slice already caps `issues_to_start`).

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (init `current_count`, thread per-repo, update final summary)
- Modified test files (9 sites across 4 files — every `monkeypatch.setattr(... .session_launch.get_active_session_count, ...)` patch site):
  - `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`
  - `tests/workflows/vscodeclaude/test_session_launch.py`
  - `tests/workflows/vscodeclaude/test_session_restart.py` (includes `test_process_eligible_issues_respects_max_sessions`, whose semantic is "already at max → return empty")
  - `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`

## WHAT
```python
# session_launch.py
def process_eligible_issues(
    repo_name: str,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    max_sessions: int,
    current_count: int,
    all_cached_issues: list[IssueData] | None = None,
    skip_github_install: bool = False,
) -> list[VSCodeClaudeSession]: ...
```

## HOW
- In `session_launch.py`:
  - Drop the import of `get_active_session_count` from `.sessions`.
  - Remove the `current_count = get_active_session_count()` line at the top of `process_eligible_issues` (line 290) — `current_count` now arrives as a parameter.
  - **Drop the `current_count += 1` line inside the inner launch loop.** It is dead bookkeeping: `issues_to_start` is already sliced to `available_slots = max_sessions - current_count`, so the local counter is never re-read after the slice. Boy Scout cleanup, included in this commit.
- In `commands.py` `execute_coordinator_vscodeclaude`:
  - After `restart_closed_sessions` returns, initialise:
    ```python
    current_count = sum(active_set.values()) + len(restarted)
    ```
    Note: `active_set` lookups elsewhere in the codebase use `.get(folder, False)`; here we use `sum(active_set.values())` which counts only the booleans actually present in the snapshot — consistent with the "missing key = inactive" convention.
  - For each iteration of `for repo_name in repo_names`, pass `current_count=current_count` into `process_eligible_issues(...)`.
  - After the call returns, increment: `current_count += len(started)`.
  - Replace the final-summary call:
    ```python
    current = get_active_session_count()
    logger.log(OUTPUT, "No new sessions started (active: %d/%d)", current, max_sessions)
    ```
    with:
    ```python
    logger.log(OUTPUT, "No new sessions started (active: %d/%d)", current_count, max_sessions)
    ```
  - Do **not** remove the `get_active_session_count` import from `commands.py` yet — that happens in step 4 along with the symbol's deletion. (If pylint flags it as unused after this step, then remove it now; otherwise leave for step 4.)

## ALGORITHM (relevant orchestration in `commands.py`)
```
restarted = restart_closed_sessions(active_set=active_set, cached_issues_by_repo=...)
current_count = sum(active_set.values()) + len(restarted)
for repo_name in repo_names:
    started = process_eligible_issues(..., current_count=current_count, ...)
    current_count += len(started)
    total_started.extend(started)
# final summary uses current_count
```

## DATA
- `current_count: int` — running count of active+restarted+newly-launched sessions across all repos in this command run.
- Return type of `process_eligible_issues` unchanged: `list[VSCodeClaudeSession]`.

## TDD: Tests first

Across the 4 test files listed in WHERE (9 sites total), every patch that looks like:
```python
monkeypatch.setattr(
    "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
    lambda: <N>,
)
# or (less common):
mock.patch("mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count", return_value=<N>)
```
becomes:
- Remove the `monkeypatch.setattr` (or `mock.patch`) of `get_active_session_count`.
- Pass `current_count=<N>` as an explicit kwarg into the `process_eligible_issues(...)` call in that test, where `<N>` matches whatever the patch was returning.

Important: `process_eligible_issues` after this step no longer calls `get_active_session_count`, so any leftover patch is a silent no-op. Every site listed in WHERE must be rewritten — partial coverage means the remaining tests exercise the real code path with whatever `get_active_session_count` returns at test time, not the value the test author intended.

Special case — `test_session_restart.py::test_process_eligible_issues_respects_max_sessions` (~line 253): this test asserts the "already at max → return empty" early-return. The patch currently returns `2` and the test sets `max_sessions=2`. The rewrite is: drop the patch, pass `current_count=2`, and keep the empty-return assertion. This is the canonical example of the rewrite preserving semantics — `current_count >= max_sessions` is exactly what the early-return checks.

Run pytest; confirm failures across all four files, then implement.

## Acceptance
- All four test files listed in WHERE pass; in particular `test_session_launch_process_issues.py`, `test_session_launch.py`, `test_session_restart.py` (including `test_process_eligible_issues_respects_max_sessions`), and `test_session_restart_branch_integration.py`.
- No `monkeypatch.setattr(... .session_launch.get_active_session_count, ...)` calls remain anywhere under `tests/workflows/vscodeclaude/` (a leftover patch on the now-uncalled function is a silent no-op and a correctness hazard).
- The dead `current_count += 1` is gone from `process_eligible_issues`.
- pylint, pytest, mypy clean (with marker exclusion).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2 exactly as described.

Apply TDD:
1. Update the 9 `get_active_session_count` patches across the four test files listed in WHERE to pass `current_count=<N>` to `process_eligible_issues(...)` instead (where `<N>` matches the value the patch was returning). Pay particular attention to `test_session_restart.py::test_process_eligible_issues_respects_max_sessions`: drop the `lambda: 2` patch and pass `current_count=2` so the "already at max" semantic is preserved. Run pytest, confirm failures.
2. Add the `current_count` parameter to `process_eligible_issues` in `session_launch.py`, remove the in-function `get_active_session_count()` call and import, and drop the dead `current_count += 1` increment inside the inner launch loop. In `commands.py`, initialise `current_count` after restart returns, thread it through the per-repo loop with `current_count += len(started)`, and update the final-summary log line.
3. Run pylint, mypy, pytest (with marker exclusion). Fix until all green. Verify no `monkeypatch.setattr(... .session_launch.get_active_session_count, ...)` calls remain under `tests/workflows/vscodeclaude/`.

Do not remove `get_active_session_count` from `sessions.py` or `__init__.py` yet — that happens in step 4. If pylint complains about an unused import in `commands.py`, drop only that one import.

Commit message: `vscodeclaude: thread current_count through process_eligible_issues`.
