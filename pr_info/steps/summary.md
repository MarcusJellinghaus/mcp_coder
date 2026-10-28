# Summary — #1352 fix(review): log the exception before failing the review as "general"

## Problem

A failed review run prints only `Error: review-implementation review failed: general`.
The exception that caused it is caught and dropped: it never reaches the console,
the issue failure comment, or MLflow. Three other "general" failures carry no
exception and no detail at all.

## Goal

- Reviewer, supervisor, fix-task and CI-gate exceptions show type + message in the
  console log (with traceback, **once**) and in the issue failure comment.
- `CalledProcessError` shows its `.stderr` (the real cause), with the Jenkins-agent
  `Stream file: <path>` suffix removed and capped at ~300 chars in the comment.
- Empty-report, unparseable-verdict and no-session-id failures name their reason in
  the comment.

## Architectural / design changes

1. **New generic helper module `mcp_coder.llm.error_summary`** (domain layer).
   It lives in `llm`, not `workflow_utils`, because `llm` sits *below*
   `workflow_utils` in import-linter (`layers` contract) and tach; #1362's
   `llm/mlflow_logger.py` will import it.
   - `summarize_exception(exc)` — `"Type: message"`; for `CalledProcessError` the
     message is the decoded `.stderr` (fallback to `f"{name}: {exc}"` when stderr is
     empty once the stream-file suffix is ignored). Full text — used for the console.
   - `comment_safe(text)` — collapse line breaks to single spaces (keeps the
     `**Error:**` field on one line), strip the trailing `Stream file: …` suffix and
     cap at `_COMMENT_LIMIT = 300` with `…`. For public issue comments only.
   - One module-level regex `_STREAM_FILE_RE = r"\s*Stream file: .*\Z"` covers all
     three suffix shapes (claude `"CLI failed with code N. Stream file: X"`, claude
     `"<msg> Stream file: X"`, copilot `"<stderr>\nStream file: X"` / `"Stream file: X"`).
2. **`workflow_utils.failure_handling.exception_summary(exc)`** — thin wrapper that
   adds the `McpServersUnavailableError` → `format_mcp_unavailable_message(exc)`
   case, else delegates to `summarize_exception`. `llm_failure_reason` is untouched
   (classifying ≠ summarising).
3. **Central logging in `_fail` (`workflows/review/handoff.py`)** — new keyword
   `exc: BaseException | None = None`. When given: one `logger.error(..., exc_info=exc)`
   with the full summary, the banner message becomes
   `"{name} review failed: {reason}: {summary}"`, and the comment's Error field is
   `details or comment_safe(summary)`. Shared by `review-plan` and
   `review-implementation`. Failure label/Category is unchanged (timeout / MCP keep
   theirs).
4. **CI gate (`workflows/review/steps.py::_after_steps`)** returns a 3-tuple
   `(reason, outcome, detail)`. Its `except` logs the traceback itself
   (`exc_info=True`) and returns `comment_safe(exception_summary(exc))` as
   `detail`. Callers pass `detail` only to `_fail(details=...)` — never to the
   committed round log, and never `exc=` (so the traceback is logged once). The
   rebase gate stays outside the `try`; `_after_steps` still never raises.
5. **Committed round log (`pr_info/…_review_log_N.md`) is unchanged** — it keeps the
   bare reason everywhere.

No new dependencies. No redaction pass (no free-text redactor exists); only the
stream-file path is stripped.

## Files

### Created
- `src/mcp_coder/llm/error_summary.py`
- `tests/llm/test_error_summary.py`
- `tests/workflows/review/test_core_failure_detail.py`

### Modified
- `src/mcp_coder/workflow_utils/failure_handling.py` — add `exception_summary`
- `tests/workflow_utils/test_failure_handling.py` — wrapper tests
- `src/mcp_coder/workflows/review/handoff.py` — `_fail(exc=)`
- `src/mcp_coder/workflows/review/core.py` — pass `exc=` at 3 catch sites, `details=`
  at 3 no-exception failures, unpack `_after_steps` 3-tuple at 2 callers
- `src/mcp_coder/workflows/review/steps.py` — `_after_steps` 3-tuple + logging
- `tests/workflows/review/test_core.py` — extend reviewer-generic and MCP tests
- `tests/workflows/review/test_core_after_steps.py` — extend the two CI-exception tests
- `tests/workflows/review/test_steps.py` — 3-tuple

## Steps

1. `llm/error_summary.py` + `failure_handling.exception_summary` (helpers only)
2. `_fail(exc=)` + the three core.py catch sites
3. `details=` for the three failures without an exception
4. `_after_steps` 3-tuple + CI-gate logging + both callers

## Out of scope

- MLflow error-message tag (#1362).
- Retrying / classifying 529 overloaded errors.
