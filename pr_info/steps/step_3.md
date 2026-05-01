# Step 3 — Thread `current_count` into `process_eligible_issues`

## Goal
Eliminate the per-repo `get_active_session_count()` call inside `process_eligible_issues`. Capacity tracking moves to the caller (`commands.py`), which threads `current_count` across the per-repo loop and updates the final summary log.

## WHERE
- Modified: `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
- Modified: `src/mcp_coder/cli/commands/coordinator/commands.py` (init `current_count`, thread per-repo, update final summary)
- Modified: `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` (7 sites)

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
  - The existing local `current_count += 1` increment on successful session launch can be kept; it is local-only and does not leak to the caller.
- In `commands.py` `execute_coordinator_vscodeclaude`:
  - After `restart_closed_sessions` returns, initialise:
    ```python
    current_count = sum(active_set.values()) + len(restarted)
    ```
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
  - Do **not** remove the `get_active_session_count` import from `commands.py` yet — that happens in step 5 along with the symbol's deletion. (If pylint flags it as unused after this step, then remove it now; otherwise leave for step 5.)

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

In `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`, the 7 sites that look like:
```python
monkeypatch.setattr(
    "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
    lambda: <N>,
)
# or:
mock.patch("mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count", return_value=<N>)
```
become:
- Remove the patch.
- Pass `current_count=<N>` as a kwarg to the `process_eligible_issues(...)` call.

If a test currently mocks `get_active_session_count` to verify the "already at max" early-return, the equivalent is now: pass `current_count=max_sessions` and assert empty return.

Run pytest; confirm failures, then implement.

## Acceptance
- All `test_session_launch_process_issues.py` tests pass.
- pylint, pytest, mypy clean (with marker exclusion).

## LLM Prompt

Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 exactly as described.

Apply TDD:
1. Update the 7 `get_active_session_count` patches in `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` to pass `current_count=...` instead. Run pytest, confirm failures.
2. Add the `current_count` parameter to `process_eligible_issues` in `session_launch.py`, remove the in-function `get_active_session_count()` call and import. In `commands.py`, initialise `current_count` after restart returns, thread it through the per-repo loop with `current_count += len(started)`, and update the final-summary log line.
3. Run pylint, mypy, pytest (with marker exclusion). Fix until all green.

Do not remove `get_active_session_count` from `sessions.py` or `__init__.py` yet — that happens in step 5. If pylint complains about an unused import in `commands.py`, drop only that one import.

Commit message: `vscodeclaude: thread current_count through process_eligible_issues`.
