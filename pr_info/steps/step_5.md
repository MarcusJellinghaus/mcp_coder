# Step 5: Rescue commit and the abort rule

Every abort from the check stage (per task and final) formats, commits with a fixed message and pushes first, so work survives a discarded Jenkins checkout. Rescue happens in one place, `core.py`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 only. Write the tests in `tests/workflows/implement/test_check_loop_rescue.py` and `test_core_check_abort.py` first, then add `rescue_commit` to `check_loop.py`, the `checks_failed` field to `TaskOutcome`, and the `abort_checks` routing in `core.py`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- `src/mcp_coder/workflows/implement/check_loop.py` (add `rescue_commit`)
- `src/mcp_coder/workflows/implement/task_processing.py` (`TaskOutcome.checks_failed`, set on check aborts)
- `src/mcp_coder/workflows/implement/core.py` (`abort_checks`)
- Tests: create `tests/workflows/implement/test_check_loop_rescue.py`, `tests/workflows/implement/test_core_check_abort.py`; extend `test_task_processing_checks.py`; adjust `test_core_final_check.py`, `test_core_failure_categories.py` and any other core test that reaches a check-stage abort (patch `rescue_commit`).

## WHAT
```python
# check_loop.py
RESCUE_COMMIT_MESSAGE = "wip(implement): checks failed ({reason})"

def rescue_commit(project_dir: Path, reason: str) -> str:
    """Format, commit and push whatever is in the tree after a check-stage abort.

    Returns one line for the failure comment:
      "pushed <sha>" | "committed <sha>, push failed" | "nothing to commit"
      | "commit failed: <error>"
    Never raises: the original failure reason must win.
    """
```
```python
# task_processing.py
@dataclass(frozen=True)
class TaskOutcome:
    success: bool
    reason: str
    detail: str = ""
    checks_failed: bool = False   # aborted in the per-task check stage
```
```python
# core.py, nested in body()
def abort_checks(reason: str, *, stage: str, message: str) -> int:
    rescue = rescue_commit(project_dir, reason)
    return fail(reason, stage=stage, message=f"{message} — rescue commit: {rescue}")
```

## HOW
- `rescue_commit` imports `commit_all_changes` from `mcp_coder.mcp_workspace_git`, `push_changes` and `run_formatters` from `mcp_coder.workflow_steps.commit`, `COMMIT_MESSAGE_FILE` from `.constants`, `read_and_clear_blocked` from `.blocked`.
- `process_single_task`: the check-stage `return TaskOutcome(False, checks.status, checks.detail)` gains `checks_failed=True`. Nothing else in it changes; exits from the main LLM call keep `checks_failed=False`.
- `process_task_with_retry` already returns non-retry outcomes unchanged.
- `core.py` task loop: right after `if not outcome.success:` and the `no_tasks` break, pick the failure function:
  ```python
  task_fail = abort_checks if outcome.checks_failed else fail
  ```
  and use `task_fail(...)` in the `blocked`, `timeout`, `mcp_unavailable` and `error` branches (same arguments as today).
- `core.py` final check: every non-clean mapping from step 4 calls `abort_checks` instead of `fail`. The rescue `reason` is the failure reason (`checks_exhausted`, `general`, `blocked`, `timeout`, `mcp_unavailable`).

## ALGORITHM (`rescue_commit`)
```
try: read_and_clear_blocked(dir); (dir / COMMIT_MESSAGE_FILE).unlink(missing_ok=True)
     try: if not run_formatters(dir): log warning   except Exception: log warning
     result = commit_all_changes(RESCUE_COMMIT_MESSAGE.format(reason=reason), dir)
     if not result["success"]: return f"commit failed: {result['error']}"
     if not result["commit_hash"]: return "nothing to commit"
     return f"pushed {sha}" if push_changes(dir) else f"committed {sha}, push failed"
except Exception as e: log; return f"commit failed: {e}"
```
`except Exception` also covers `FormatterConfigError` and the typed LLM failures; use `# pylint: disable=broad-exception-caught`.

## DATA
- `rescue_commit` returns a single-line string; it is appended to the failure message.
- `TaskOutcome.checks_failed: bool = False`.

## Tests (write first)

`test_check_loop_rescue.py` (patch `run_formatters`, `commit_all_changes`, `push_changes` in `check_loop`; use `tmp_path` for the files):
- commit message is exactly `wip(implement): checks failed (general)`.
- a blocked marker and `pr_info/.commit_message.txt` in `tmp_path` are deleted before `commit_all_changes` is called.
- `run_formatters` returning `False` → still commits.
- `run_formatters` raising `FormatterConfigError` → still commits.
- outcomes: pushed with sha; `push_changes` returning `False` → "push failed"; `commit_hash=None` with success → "nothing to commit"; `success=False` → "commit failed: <error>".
- `commit_all_changes` / `push_changes` raising (including `LLMTimeoutError`) → returns a string, does not raise.

`test_task_processing_checks.py`: check-stage aborts set `checks_failed=True`; an empty LLM response from the main call and a blocked main call keep `checks_failed=False` and never call `rescue_commit` / `commit_changes` (`test_blocked_wins_over_changed_files` must still pass).

`test_core_check_abort.py` (patch `rescue_commit` in `core`, `_fail` or `handle_workflow_failure`):
- per-task outcome with `checks_failed=True` for each of `error`, `blocked`, `timeout`, `mcp_unavailable` → `rescue_commit` called once, failure reason unchanged (`error` → `general`), message ends with `— rescue commit: pushed abc1234`.
- the same reasons with `checks_failed=False` → `rescue_commit` not called.
- final check `cap` → `rescue_commit(project_dir, "checks_exhausted")` and failure `checks_exhausted`.
- final check `error` → `general`; `blocked` → `blocked`; `timeout` → `timeout`, each after a rescue.
- `rescue_commit` returning "commit failed: x" still fails with the original reason.
- final check `ValueError` from the config (outcome `error` with the config message) → `general` with that message.

Existing core tests: `rescue_commit` lives in `check_loop`, so patches of `core.run_formatters` / `core.push_changes` don't stop it from running real formatters and git calls on `/test/project`. Patch `mcp_coder.workflows.implement.core.rescue_commit` (e.g. `return_value="pushed abc1234"`) in every existing core test where the final check ends non-clean or a task outcome has `checks_failed=True`. This includes the final-check `timeout` / `mcp_unavailable` tests in `test_core_failure_categories.py` (~lines 71 and 137, converted to `CheckOutcome` in step 4) and the `test_core_final_check.py` tests from step 4. Assertions on the exact failure message must allow the new `— rescue commit: …` suffix (use `startswith` / `in`, or include the suffix). Keep `test_core_workflow.py` under 750 lines.
