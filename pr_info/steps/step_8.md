# Step 8 — Review `_route_to_human` → structured "Handed Off" comments

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 8** exactly as described in
> `pr_info/steps/step_8.md`. If `RebaseOutcome` does not exist in
> `src/mcp_coder/workflow_steps/rebase.py` or `_after_steps` does not return a
> tuple, write one line to `pr_info/.blocked.txt` and stop. Tests first, then
> implementation. Run pylint, pytest (fast unit set, `-n auto`), mypy and
> `check_file_size`; all must pass (`review/core.py` must stay under 750 lines).
> One commit.

## WHERE

- `src/mcp_coder/workflows/review/handoff.py` — `_route_to_human`, `_REBASE_HANDOFF`
- `src/mcp_coder/workflows/review/core.py` — four `_route_to_human` call sites, name the outcome at both `_after_steps` sites
- `src/mcp_coder/workflows/review/steps.py` — replace the `#1066` placeholder comment, INFO log → WARNING
- `docs/processes-prompts/development-process.md:1185` — escalation sentence
- Tests: `tests/workflows/review/test_handoff_route.py`, `test_core.py`, `test_core_after_steps.py` (incl. rewrite of `:125-129`)

## WHAT

```python
# reason -> (Category, Next step)
_REBASE_HANDOFF: dict[str, tuple[str, str]] = {
    "dirty_tree": ("Uncommitted changes",
                   "Commit or discard the listed files, then re-run the review"),
    "no_base": ("Base branch not detected",
                "Add a `### Base Branch` section to the issue, then re-run"),
    "base_missing": ("Base branch missing on origin",
                     "Push or restore the base branch, or fix `### Base Branch`, then re-run"),
    "conflict": ("Rebase conflict", "`/rebase`, then re-run the review"),
    "rebase_failed": ("Rebase failed",
                      "`/rebase` (may be a conflict that only appears while replaying commits); check the job log"),
    "push_failed": ("Push failed after rebase",
                    "Fetch, check for foreign commits, then `git push --force-with-lease`"),
}
_REBASE_REASON = "Branch could not be rebased cleanly onto its base"

def _route_to_human(
    config: ReviewConfig,
    project_dir: Path,
    *,
    issue_number: int | None,
    update_issue_labels: bool,
    post_issue_comments: bool,
    log_path: Path | None,
    round_number: int,
    start_time: float,
    category: str | None = None,
    reason: str | None = None,
    rebase: RebaseOutcome | None = None,
) -> int:   # comment_body removed
```

## HOW

- `handoff.py` imports `RebaseOutcome` from `mcp_coder.workflow_steps.rebase`,
  `build_failure_comment` from `failure_handling`, and `time`.
- Remove the `f"❌ {comment_body}"` prefixing — the builder owns `❌`.
- Order inside `_route_to_human`: flush → banner → build comment → post (gated) →
  escalate label. Never a failure label; always returns `0`.
- Warning banner (mirrors `handle_workflow_failure`):
  `"=" * 60`, `REVIEW HANDED OFF`, `Lane: <display_name>`, `Reason: <reason>`,
  `Round: <n>`, `Target label: <escalate_label_id>`, `"=" * 60`.
- Call sites in `review/core.py`:
  - dismiss rebase + mid-loop rebase: `reason, rebase_outcome = _after_steps(...)`;
    `_route_to_human(..., round_number=round_number, start_time=start_time, rebase=rebase_outcome)`
  - escalate verdict: `category="Escalated by supervisor", reason=verdict.escalate_reason, round_number=round_number`
  - rounds cap: `category="Round limit reached", reason=f"{REVIEW_MAX_ROUNDS} rounds without converging", round_number=REVIEW_MAX_ROUNDS` (not the loop variable — pylint `undefined-loop-variable`)
- `steps.py`: replace the `NotYetImplemented (#1066)` comment with a short note that
  an LLM conflict-resolving rebase attempt is #1266's follow-up; change the
  `logger.info(...)` to `logger.warning("Rebase gate did not pass (%s); routing to needs-human", outcome.reason)`.
- Update `_route_to_human` / `run_review_workflow` docstrings that mention
  `comment_body`.
- Docs: replace "(no separate issue comment is posted for escalations)" with a
  sentence saying escalations, rebase hand-offs and the rounds cap post a
  structured `## ❌ <Lane> Handed Off` comment and apply the escalate label.

## ALGORITHM (`_route_to_human`)

```
if log_path is not None: _flush_round_log(project_dir, only=log_path)
if rebase is not None and rebase.reason in _REBASE_HANDOFF:
    category, next_step = _REBASE_HANDOFF[rebase.reason]; reason = _REBASE_REASON
fields = [("Category", category), ("Stage", f"{config.display_name}, round {round_number}"),
          ("Reason", reason), ("Base", _base_value(rebase)),
          ("Likely conflicting files" if rebase.reason == "conflict" else "Uncommitted files", files),
          ("Next step", next_step)]          # file field only when rebase has files
log banner; body = build_failure_comment(project_dir, title=config.display_name,
    kind="Handed Off", fields=fields, elapsed=time.time() - start_time); post; set label
```

`_base_value(rebase)`: `None` when no `base_branch`; `f"origin/{b} @ {sha}"` when
sha known; `f"origin/{b}"` otherwise (`base_missing`). Files rendered as
`", ".join(f"`{f}`" for f in files)`.

## DATA

Example (conflict):

```
## ❌ Implementation Review Handed Off
**Category:** Rebase conflict
**Stage:** Implementation Review, round 2
**Reason:** Branch could not be rebased cleanly onto its base
**Branch:** 1268-feat @ abc1234
**Base:** origin/main @ def5678
**Likely conflicting files:** `src/a.py`, `src/b.py`
**Next step:** `/rebase`, then re-run the review
**Elapsed:** 12m 3s
```

## Tests

- `test_handoff_route.py`: replace `comment_body="handing off"` with the new
  kwargs (`round_number=1, start_time=time.time(), category="X", reason="Y"`);
  assert returns `0`, escalate label only, comment first line
  `## ❌ <Lane> Handed Off` (no `❌ ##`), flush happens before the comment
  (call order via a shared `MagicMock` parent or `side_effect` list), and the
  warning banner (`caplog`, `REVIEW HANDED OFF`).
- Parametrised over every `_REBASE_HANDOFF` reason: Category and Next step
  match the table; `/rebase` never appears for `dirty_tree` / `push_failed`;
  Base line present with sha for `conflict` / `rebase_failed` / `push_failed`,
  `origin/<base>` without sha for `base_missing`, absent for `dirty_tree` /
  `no_base`; `Likely conflicting files` only for `conflict`, `Uncommitted files`
  only for `dirty_tree`.
- `test_core.py` / `test_core_after_steps.py`: escalate → Category
  `Escalated by supervisor` + Reason = escalate reason; rounds cap → `Round limit
  reached`, `5 rounds without converging`, Stage `…, round 5`; dismiss / mid-loop
  rebase pass the outcome through (Category `Rebase conflict` for the conftest
  conflict outcome).
- Rewrite `test_rebase_slot_references_issue_1066` (`test_core_after_steps.py:125-129`)
  as a behaviour test: a non-ok outcome makes `_after_steps` return
  `("rebase", outcome)` and logs a warning naming `outcome.reason` — no
  source-text assertion.
