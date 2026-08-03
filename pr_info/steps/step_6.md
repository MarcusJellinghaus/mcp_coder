# Step 6 — Handoff wiring: cap → escalate, flush every terminal path

See `pr_info/steps/summary.md` (§"Failure-reason convention", §"`_flush_round_log` = commit
+ push only"). Adds the two handoff helpers and rewires `core.body()`'s terminal paths so
the rounds cap hands off (RC=0) instead of failing, and every terminal path commits its
last round's log.

## WHERE
- `src/mcp_coder/workflows/review/handoff.py` — add `_flush_round_log`, `_route_to_human`.
- `src/mcp_coder/workflows/review/core.py` — rewire the dismiss / escalate / rebase / cap /
  commit-failed / push-failed branches.
- New test: `tests/workflows/review/test_handoff.py`.
- Update: `tests/workflows/review/test_core.py`, `test_core_after_steps.py`.

## WHAT
```python
def _flush_round_log(project_dir: Path, message: str = "Add review round log") -> None:
    """Commit + push the already-written round log; best-effort (never raises)."""

def _route_to_human(config, project_dir, *, issue_number, update_issue_labels,
                    post_issue_comments, comment_body) -> int:
    """Flush log, post an issue comment (gated), set escalate label, return 0."""
```

## HOW
- `_flush_round_log`: `commit_all_changes(message, project_dir)` (imported from
  `mcp_coder.mcp_workspace_git`) then `push_changes(project_dir)`. Wrap both in try/except
  and on failure `logger.warning(...)` — **never recurse** into another failure. Does **not**
  call `write_round_log` (the caller writes first; see the cap note below).
- `_route_to_human`: `_flush_round_log(project_dir)` → if `post_issue_comments and
  issue_number is not None`, `IssueManager(project_dir).add_comment(issue_number,
  comment_body)` (best-effort) → `_set_label(config, project_dir,
  config.escalate_label_id, update_issue_labels)` → `return 0`.
- **core rewiring:**
  - *dismiss (success)*: after `write_round_log(..., "dismiss")`, call
    `_flush_round_log(project_dir)` before `_set_label(success)` — so the terminal dismiss
    log is committed.
  - *escalate verdict* / *dismiss→rebase* / *tasks→rebase*: `write_round_log(...)` then
    `return _route_to_human(..., comment_body=<reason>)` (replaces the inline
    `_set_label(escalate) + return 0`).
  - *rounds cap*: the last `tasks` round already wrote its log at the end of the loop body,
    so **do not write again** — branch on the CI note:
    ```
    if pending_ci_note: return _fail(..., "ci", ...)     # CI stays terminal (17f-ci)
    return _route_to_human(..., comment_body="rounds cap reached")
    ```
  - *commit-failed* / *push-failed*: keep `write_round_log(...)` + `_fail(...)`, and add a
    best-effort `_flush_round_log(project_dir)` between them (committing is what is broken,
    so this is best-effort by design).
- Comment bodies: short, human-readable, e.g. cap → "Automated {config.name} review reached
  the round limit ({REVIEW_MAX_ROUNDS} rounds) without converging — handing off for human
  review."; escalate → include `verdict.escalate_reason`; rebase → "Branch could not be
  rebased cleanly — handing off."

## ALGORITHM (`_route_to_human`)
```
_flush_round_log(project_dir)
if post_issue_comments and issue_number is not None:
    try: IssueManager(project_dir).add_comment(issue_number, comment_body)
    except Exception: logger.warning(...)
_set_label(config, project_dir, config.escalate_label_id, update_issue_labels)
return 0
```

## DATA
`_flush_round_log -> None` (best-effort). `_route_to_human -> int` (always `0`).

## TDD
- `test_handoff.py`: `_flush_round_log` calls `commit_all_changes` + `push_changes`, and
  swallows a commit/push failure (patch both, assert no raise, assert warning). `_route_to_human`
  flushes, posts a comment only when `post_issue_comments` and `issue_number` are set,
  transitions to `escalate_label_id`, and returns `0`.
- `test_core.py` (plan lane): update the old `test_rounds_cap_exhausted_fails` →
  **cap now returns `0`**, sets the `plan_review` (escalate) label, posts an issue comment,
  and `handle_workflow_failure` is **not** called; the last round appears in the committed
  log (assert `commit_all_changes`/flush invoked).
- Escalate / rebase paths: assert they now flush and (handoff paths) post a comment, while
  keeping their existing labels and exit codes.
- `test_core_after_steps.py` (impl lane): cap with `pending_ci_note` set still fails to the
  `code_review_ci` label (RC=1) — CI stays terminal.

## LLM PROMPT
> Implement Step 6 from `pr_info/steps/step_6.md` (see `pr_info/steps/summary.md`). Add
> `_flush_round_log` (commit_all_changes + push_changes, best-effort, no re-write) and
> `_route_to_human` (flush → gated issue comment → escalate label → return 0) to
> `workflows/review/handoff.py`. Rewire `core.body()`'s terminal branches: dismiss-success
> flushes before setting the success label; escalate/rebase paths route through
> `_route_to_human`; the rounds cap returns `_fail(..., "ci")` when `pending_ci_note` is set
> else `_route_to_human(...)` (do NOT re-write the cap round's log — it was already written);
> commit-failed/push-failed add a best-effort flush before `_fail`. Write `test_handoff.py`
> and update the cap/escalate/rebase tests first, then implement. Run pylint, pytest
> (`-n auto` with integration exclusions), and mypy. One commit.
