# Step 7 — Implement: auth at the task call, fix turn and final check

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md` only. Steps 1–6
> are done. Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit
> markers), mypy; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/workflows/implement/failure_reporting.py`: `FAILURE_LABELS`, `CATEGORY_DISPLAY`.
- `src/mcp_coder/workflows/implement/check_loop.py`: `CheckStatus`, `_fix_turn`, and the
  `CheckOutcome` / `check_and_fix` docstrings.
- `src/mcp_coder/workflows/implement/task_processing.py`: `process_single_task`, and the
  `process_task_with_retry` docstring.
- `src/mcp_coder/workflows/implement/core.py`: the task-loop branch and `_final_check_failure`.
- Tests:
  - Create `tests/workflows/implement/test_core_auth.py` for the core routing. Follow the
    patching style of `test_core_failure_routing.py` / `test_core_check_abort.py` /
    `test_core_final_check.py`.
  - Add unit cases to `test_failure_reporting.py`, `test_check_loop_fix_turns.py` and
    `test_task_processing.py`. If any would exceed 750 lines, put those cases in
    `test_core_auth.py` instead.

## WHAT

```python
# failure_reporting.py
FAILURE_LABELS["auth"] = "implementing_failed"   # shares the general label (like checks_exhausted)
CATEGORY_DISPLAY["auth"] = "Auth"

# check_loop.py
CheckStatus = Literal["clean", "cap", "error", "blocked", "timeout", "mcp_unavailable", "auth"]
```

## ALGORITHM

```
# check_loop._fix_turn — extend the existing tuple
except (LLMAuthError, LLMTimeoutError, McpServersUnavailableError) as e:
    blocked = read_and_clear_blocked(project_dir)
    status = cast(CheckStatus, llm_failure_reason(e) or "timeout")
    detail = append_detail(exception_summary(e), blocked) if status == "auth" else blocked or ""
    return CheckOutcome(status, detail)

# task_processing.process_single_task — extend the existing tuple
except (LLMAuthError, LLMTimeoutError, McpServersUnavailableError) as e:
    llm_error = llm_failure_reason(e) or "error"
    if llm_error == "auth": llm_detail = exception_summary(e)     # llm_detail = "" before try
...
if llm_error == "auth": return TaskOutcome(False, "auth", append_detail(llm_detail, blocked or ""))
if llm_error in ("timeout", "mcp_unavailable"): ...   # unchanged

# core.run_implement_workflow task loop, next to the mcp_unavailable branch
if outcome.reason == "auth":
    # Task call -> fail; per-task fix turn (checks_failed) -> abort_checks (rescue commit)
    return task_fail("auth", stage="Task implementation", message=outcome.detail)

# core._final_check_failure, before the generic fallback
if checks.status == "auth": return "auth", checks.detail
```

## HOW

- Imports:
  - `LLMAuthError` from `mcp_coder.llm.interface`
  - `exception_summary` from `mcp_coder.workflow_utils.failure_handling` (already imported for `llm_failure_reason`)
  - `append_detail` from `.failure_reporting` in `check_loop.py` and `task_processing.py`

  If lint-imports or pylint reports a cycle for `append_detail`, use the inline f-string
  `f"{text} (agent reported: {blocked})" if blocked else text` instead.
- The per-task check path needs no change: `task_processing` already returns any non-clean,
  non-cap status as `TaskOutcome(False, status, detail, checks_failed=True)`.
- Update the comment "Categorize the two typed LLM failures" in `task_processing.py` to
  "the typed LLM failures (see `llm_failure_reason`)".
- Docstrings: add `auth` to the reason lists in `process_single_task`, `process_task_with_retry`,
  `CheckOutcome` and `check_and_fix`. The detail carries the error text (plus any blocked
  marker) for `auth`.

## DATA

- `TaskOutcome(False, "auth", "<LLMAuthError: hint + CLI text>[ (agent reported: …)]", checks_failed=False|True)`.
- `CheckOutcome("auth", "<LLMAuthError: …>[ (agent reported: …)]")`.
- Rescue commit message on a fix-turn or final-check auth: `wip(implement): checks failed (auth)`.

## Tests (first)

- `FAILURE_LABELS["auth"] == "implementing_failed"`, `CATEGORY_DISPLAY["auth"] == "Auth"`;
  `test_labels_and_display_share_keys` passes.
- `_fix_turn` with `prompt_llm` raising `LLMAuthError(AUTH_MESSAGE)` → `CheckOutcome("auth", detail)`,
  where `detail` contains the hint; with a blocked marker present, the marker text is appended.
- `process_single_task` with `prompt_llm` raising `LLMAuthError` →
  `TaskOutcome(success=False, reason="auth", checks_failed=False)`, with the detail containing
  the hint.
- core (`test_core_auth.py`):
  - **Task-call auth**: `process_task_with_retry` returns `TaskOutcome(False, "auth", "LLMAuthError: …")`
    → the workflow returns 1 after one round; `_fail` gets reason `auth`, stage
    "Task implementation", and the message with the hint; no rescue commit; the label is
    `implementing_failed`.
  - **Per-task fix-turn auth**: `TaskOutcome(False, "auth", "...", checks_failed=True)` →
    `rescue_commit(project_dir, "auth")` is called, then fail with reason `auth`.
  - **Final-check auth**: `check_and_fix` returns `CheckOutcome("auth", "LLMAuthError: …")` →
    `rescue_commit` is called with `"auth"`; the message does not contain `"agent reported"`
    unless a marker exists.
  - No fall-through: the loop is not re-entered after an `auth` outcome (assert
    `process_task_with_retry` call count == 1).
