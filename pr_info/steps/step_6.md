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
  `mcp_coder.mcp_workspace_git`) then `push_changes(project_dir)`. Neither call raises on a
  normal failure — `commit_all_changes` returns `{"success": bool}` and `push_changes`
  returns `bool` — so **check the return value** of each and `logger.warning(...)` when it is
  falsy (`not result["success"]` / `not push_changes(...)`); skip the push when the commit
  did not succeed. Additionally guard both calls with a broad `try/except` that only
  `logger.warning(...)`s, to swallow an unexpected raise. Either way **never recurse** into
  another failure. Does **not** call `write_round_log` (the caller writes first; see the cap
  note below).
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
    if pending_ci_note:
        _flush_round_log(project_dir)                    # commit the last round's log
        return _fail(..., "ci", ...)                     # CI stays terminal (17f-ci)
    return _route_to_human(..., comment_body="rounds cap reached")
    ```
    The best-effort `_flush_round_log` before `_fail(..., "ci")` mirrors the
    commit-failed / push-failed paths below: the CI-cap is a terminal path too, so the
    last round's log must land in the committed review log (AC: "the last executed round
    always appears in the committed review log, on every terminal path"). The
    `_route_to_human` branch flushes internally.
  - *commit-failed* / *push-failed*: keep `write_round_log(...)` + `_fail(...)`, and add a
    best-effort `_flush_round_log(project_dir)` between them (committing is what is broken,
    so this is best-effort by design).
  - *dismiss→after-steps failure* (dismiss branch, `if reason: return _fail(reason)` — e.g.
    impl-lane dismiss verdict whose final CI gate is red → `17f-ci`, or `timeout` / `general`
    / `mcp_unavailable`): this branch currently returns `_fail` **without** writing a round
    log at all. Add `write_round_log(..., changes=reason, escalate_reason=reason)` **and** a
    best-effort `_flush_round_log(project_dir)` before `return _fail(...)`, mirroring the
    commit-failed / push-failed handling, so the terminal round lands in the committed log.
  - *tasks→after-steps failure* (tasks branch, `elif reason: return _fail(reason)` — the
    non-`rebase`, non-`ci` after-steps reasons `timeout` / `general` / `mcp_unavailable`):
    same gap — no round log is written today. Add `write_round_log(..., changes=reason,
    escalate_reason=reason)` **and** a best-effort `_flush_round_log(project_dir)` before
    `return _fail(...)`. (The `ci` reason sets `pending_ci_note` and keeps looping, so it is
    unaffected; the fix was already committed earlier in the round, so the flush here commits
    only the round-log write.)
  - *tasks→resume LLM-exception* (tasks branch, the `except` around the task-application
    `reviewer._run_reviewer(...)` resume at `core.py:387`, `return _fail(llm_failure_reason(...)`
    → `general` / `timeout` / `mcp_unavailable`): this is a **terminal path on which a real
    report *and* a `tasks` verdict already exist** — the reviewer crashed only while applying
    the fixes — yet no round log is written today, so the last executed round's findings are
    lost, contrary to the AC. Add `write_round_log(..., changes=reason, escalate_reason=reason)`
    **and** a best-effort `_flush_round_log(project_dir)` before `return _fail(...)`, mirroring
    the after-steps `_fail` sub-paths above. (The other in-round `_fail` exits — the fresh
    reviewer exception, empty-report exhaustion, supervisor exception, and unparseable verdict
    — have no completed report+verdict pair and are intentionally left as-is.)
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
- `test_handoff.py`: `_flush_round_log` calls `commit_all_changes` then `push_changes`, and
  is best-effort — patch both to a falsy return (`{"success": False}` / `False`) and assert
  it does not raise and `logger.warning` fires; patch both to raise and assert it still does
  not propagate; on a falsy commit result assert `push_changes` is skipped. `_route_to_human`
  flushes, posts a comment only when `post_issue_comments` and `issue_number` are set,
  transitions to `escalate_label_id`, and returns `0`.
- `test_core.py` (plan lane): update the old `test_rounds_cap_exhausted_fails` →
  **cap now returns `0`**, sets the `plan_review` (escalate) label, posts an issue comment,
  and `handle_workflow_failure` is **not** called; the last round appears in the committed
  log (assert `commit_all_changes`/flush invoked).
- Escalate / rebase paths: assert they now flush and (handoff paths) post a comment, while
  keeping their existing labels and exit codes.
- `test_core_after_steps.py` (impl lane): cap with `pending_ci_note` set still fails to the
  `code_review_ci` label (RC=1) — CI stays terminal — **and** the last round's log is flushed
  to the committed review log (assert `_flush_round_log` / `commit_all_changes` invoked before
  `_fail`), matching the AC "the last executed round always appears in the committed review
  log, on every terminal path".
- `test_core_after_steps.py` (impl lane) — the two in-loop `_fail` sub-paths now flush:
  - *dismiss→CI-red*: supervisor returns `dismiss`, `_after_steps(is_dismiss=True)` returns
    `"ci"` → run still fails to `code_review_ci` (RC=1), **and** the round's log is written and
    flushed to the committed log (assert `write_round_log` + `_flush_round_log` /
    `commit_all_changes` invoked before `_fail`).
  - *tasks→after-steps `general`* (e.g. `_after_steps` returns `"timeout"`/`"general"` after a
    committed fix): run fails with the matching label (RC=1) **and** the round's log is written
    and flushed. Both prove the AC "the last executed round always appears in the committed
    review log, on every terminal path" holds for the `_fail` sub-paths too.
  - *tasks→resume LLM-exception*: supervisor returns `tasks`, the task-application
    `reviewer._run_reviewer(...)` resume raises (patch it to raise) → run fails with the
    mapped label (RC=1) **and** the round's log (with the real `report` findings + the `tasks`
    verdict) is written and flushed (assert `write_round_log` + `_flush_round_log` /
    `commit_all_changes` invoked before `_fail`), so a crash while applying fixes still lands
    the executed round in the committed log.

## LLM PROMPT
> Implement Step 6 from `pr_info/steps/step_6.md` (see `pr_info/steps/summary.md`). Add
> `_flush_round_log` (commit_all_changes + push_changes, best-effort, no re-write) and
> `_route_to_human` (flush → gated issue comment → escalate label → return 0) to
> `workflows/review/handoff.py`. Rewire `core.body()`'s terminal branches: dismiss-success
> flushes before setting the success label; escalate/rebase paths route through
> `_route_to_human`; the rounds cap flushes the log then returns `_fail(..., "ci")` when
> `pending_ci_note` is set else `_route_to_human(...)` (do NOT re-write the cap round's log —
> it was already written; flush = commit+push only);
> commit-failed/push-failed add a best-effort flush before `_fail`; the dismiss-branch
> `if reason: return _fail(reason)`, the tasks-branch `elif reason: return _fail(reason)`
> after-steps-failure sub-paths, AND the tasks-branch task-application resume `except`
> (`core.py:387`, where a report + `tasks` verdict already exist) — all of which today write
> no log — add `write_round_log(...)` + a best-effort flush before `_fail`, so every terminal
> path with a completed round lands it in the committed log. `_flush_round_log` must
> check the falsy return of `commit_all_changes`/`push_changes` (they do not raise) and warn.
> Write `test_handoff.py`
> and update the cap/escalate/rebase tests first, then implement. Run pylint, pytest
> (`-n auto` with integration exclusions), and mypy. One commit.
