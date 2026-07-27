# Step 5 — Enhance `review` (guard + broadened excepts + empty-report retry + rename + enriched comment)

**Reference:** `pr_info/steps/summary.md` §review. Depends on Step 1 (independent of
Steps 2/3/4). This is the direct fix for the #1042 silent `review-plan` death and covers both
`review-plan` and `review-implementation` (one `run_review_workflow`). One commit.

## WHERE

- Modify `src/mcp_coder/workflows/review/config.py` (rename reason key)
- Modify `src/mcp_coder/workflows/review/core.py`
- Modify `tests/workflows/review/test_core.py`, `.../test_core_after_steps.py`

## WHAT

- `config.py`: in **both** `REVIEW_IMPLEMENTATION.failure_labels` and
  `REVIEW_PLAN.failure_labels`, rename key `"mcp"` → `"mcp_unavailable"` (values unchanged:
  `code_review_mcp` / `plan_review_mcp`).
- `core.py`:
  - Delete `_reason_for_exception`; import `llm_failure_reason` from
    `workflow_utils.failure_handling`.
  - `EMPTY_REPORT_RETRIES = 3` (module constant).
  - Wrap the round loop in `run_guarded`.
  - Enrich `_fail(config, project_dir, reason, *, update_issue_labels, post_issue_comments,
    round_number=None, verdict=None, elapsed=None) -> int`.

## HOW

- **Structure:** resolve `issue_number, base_branch = _resolve_context(...)` and
  `start_time = time.time()` at the top, then move the whole `for round_number in range(...)`
  loop and the trailing rounds-cap `_fail` into a nested `def body() -> int:`. Return
  `run_guarded(body, project_dir=project_dir, from_label_id=config.busy_label_id,
  general_category=config.failure_labels["general"],
  comment_header=f"❌ {config.name} review terminated unexpectedly",
  update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments,
  issue_number=issue_number)`.
- **Broaden the LLM excepts** (fresh reviewer, supervisor verdict, task-apply reviewer): replace
  each `except (LLMTimeoutError, McpServersUnavailableError) as exc: return _fail(config,
  project_dir, _reason_for_exception(exc), …)` with
  `except Exception as exc: return _fail(config, project_dir, llm_failure_reason(exc) or "general",
  …, round_number=round_number, verdict=last_verdict, elapsed=time.time()-start_time)`.
- **`_after_steps` CI gate:** replace the two `except LLMTimeoutError → "timeout"` /
  `except McpServersUnavailableError → "mcp"` with a single
  `except Exception as exc: return llm_failure_reason(exc) or "general"`, scoped **only** to the
  `check_and_fix_ci(...)` call (leave the rebase gate and the branch-empty `return None` path
  outside it). Rename the literal `"mcp"` return to `"mcp_unavailable"`. The `"rebase"` / `"ci"`
  control-flow returns are untouched. (Load-bearing: `llm_failure_reason` returns
  `"mcp_unavailable"`, so the config-key rename must land in the same commit.)
- **Empty-report retry:** wrap the *fresh* reviewer call (the `tasks=None` invocation) in a
  bounded inner loop that re-invokes on a whitespace-only `report_response["text"]`, up to
  `EMPTY_REPORT_RETRIES`; on exhaustion `return _fail(config, project_dir, "general", …,
  round_number=round_number, elapsed=…)`. It does **not** touch `round_number` (inner retry, no
  round consumed). Never retries on exception (those are caught by the broadened `except` and
  fail immediately, categorized).
- **Enriched `_fail`:** track a `last_verdict` local (updated when a verdict is parsed). Extend
  the comment: base `❌ {message}` plus, when provided, `Round: {round_number}`,
  `Verdict: {verdict.decision}`, `Elapsed: {format_elapsed_time(elapsed)}`. Pass
  `round_number`/`verdict`/`elapsed` from every deliberate `_fail` call site (all lexically inside
  the loop where these are live locals; the rounds-cap call passes `round_number=REVIEW_MAX_ROUNDS`).

## ALGORITHM — fresh reviewer with empty-report retry (inner, no round consumed)

```
for _ in range(EMPTY_REPORT_RETRIES):
    try: report_response = _run_reviewer(..., session_id=None, tasks=None, ci_note=pending_ci_note)
    except Exception as exc: return _fail(config, project_dir, llm_failure_reason(exc) or "general", round_number=round_number, ...)
    if report_response["text"].strip(): break
else:
    return _fail(config, project_dir, "general", round_number=round_number, elapsed=time.time()-start_time, ...)
```

## DATA

- `_fail(...) -> int` (always `1`); comment enriched with round/verdict/elapsed when supplied.
- `run_review_workflow` / `run_guarded` → `int`.
- `config.failure_labels` key set now uses `"mcp_unavailable"` (was `"mcp"`).
- `EMPTY_REPORT_RETRIES = 3`.

## TESTS (write first)

`test_core.py`:
- Inject a generic `RuntimeError` at the fresh-reviewer call → `_fail` with the **general**
  label (`plan_review_failed` / `code_review_failed`) + comment + exit `1` (not an uncaught
  escape).
- Inject 3 whitespace-only reviewer reports → the reviewer is re-invoked as an **inner** retry
  (assert call count, `round_number` unchanged), then general-labeled failure.
- Inject `LLMTimeoutError` / `McpServersUnavailableError` at reviewer or supervisor → labels
  `*_timeout` / `*_mcp` (confirms the `"mcp"`→`"mcp_unavailable"` rename is wired end-to-end).
- Body escape / `SystemExit` → labeled via the guard (general) + comment.
- A deliberate `_fail` carries round number, last verdict, elapsed in the comment.

`test_core_after_steps.py`:
- Inject a generic exception inside the CI gate at a point that **escapes** `check_and_fix_ci`
  (not the swallowed analysis phase) → `code_review_failed` + comment, not an uncaught escape.
- Assert `"rebase"` and `"ci"` control-flow reasons still route (escalate / carry-forward),
  i.e. **not** swallowed by the broadened `except`.

## Verify

`run_pylint_check`, `run_pytest_check` (`-n auto` + unit-exclusion markers), `run_mypy_check`,
`run_lint_imports_check`.

## LLM Prompt

> Implement Step 5 of `pr_info/steps/summary.md` per `pr_info/steps/step_5.md`. Enhance the shared
> review engine: rename the `"mcp"` failure-label key to `"mcp_unavailable"` in both configs;
> delete `_reason_for_exception` and use `llm_failure_reason`; wrap the round loop in `run_guarded`
> (general = `config.failure_labels["general"]`); broaden every LLM `except` (fresh reviewer,
> supervisor verdict, task-apply reviewer, and the `check_and_fix_ci` call in `_after_steps` —
> scoped so it does not swallow the `"rebase"`/`"ci"` reasons) to categorize generic exceptions via
> `llm_failure_reason(exc) or "general"`; add a bounded inner empty-reviewer-report retry (N=3, no
> round consumed) that fails general on exhaustion; and enrich `_fail`'s comment with round number,
> last verdict, and elapsed time (plain args, no mutable handle). Follow TDD — add the generic-
> exception, empty-report-retry, timeout/mcp rename, CI-gate-escape, control-flow-preservation, and
> guard-net tests first, then implement. Run pylint, pytest (`-n auto` with unit-exclusion markers),
> mypy, and lint-imports. Produce exactly one commit.
