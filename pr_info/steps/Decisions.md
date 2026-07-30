# Decisions — Issue #1068 plan update

Decisions from the tech-lead plan review (findings 1, 2, 3, 5). Applied via
`/plan_update`.

## Decision 5 (finding 5) — Gate PR-feedback threading to the implementation lane

- **Decided:** Option B — thread PR review feedback only in the
  **implementation lane**, via a new `ReviewConfig` boolean field
  (`thread_pr_feedback`), aligned with the existing `inject_base_branch` /
  `run_after_steps` config split. The **plan lane** skips the
  `collect_branch_status` GitHub call entirely.
- **Rationale:** the shared review core loop serves both `review-plan` and
  `review-implementation`; feeding PR feedback to plan review is out of scope and
  would fire an unnecessary GitHub call.
- **Plan effect:** Step 3 rewritten — new `thread_pr_feedback` field on
  `ReviewConfig` (`True` for `REVIEW_IMPLEMENTATION`, `False` for `REVIEW_PLAN`);
  the per-round `collect_branch_status` + feedback threading is guarded behind
  the flag; both feed targets (reviewer `pr_note`, supervisor context) remain
  None-guarded. Tests assert the plan lane does NOT call `collect_branch_status`
  and the implementation lane does. Summary point 5 updated.

## Decision 1 (finding 1) — Document the CLI changes

- **Decided:** Step 2 must also update docs. Add `--fail-on-reviews` to the
  `check branch-status` options in `docs/cli-reference.md`; widen the exit-code-2
  meaning to also cover "reviews undeterminable" (not only technical error); and
  fix the `execute_check_branch_status` docstring's "2 for technical error"
  wording.
- **Plan effect:** Step 2 gains a DOCS section, an added WHERE entry, and a new
  LLM-prompt task.

## Decision 2 (finding 2) — Keep `create_empty_report` in the re-export surface

- **Decided:** Retain `create_empty_report` in the shim re-exports (it is listed
  in the issue's Decisions table), even though no mcp-coder caller consumes it
  directly.
- **Plan effect:** Step 1 gains a one-line note clarifying the retention resolves
  the apparent tension with the "re-export only consumed names" principle.

## Decision 3 (finding 3) — Name the reviewer test file explicitly

- **Decided:** The `_run_reviewer` `pr_note` kwarg tests live in
  `tests/workflows/review/test_reviewer.py` (tests mirror src), not a vague
  "extend tests/workflows/review/". Backfilling `ci_note` coverage is optional,
  not required scope.
- **Plan effect:** Step 3 TESTS section and summary test list name the file
  explicitly; the optional `ci_note` backfill is called out as optional.

## Round-2 plan review

### R2-1 — Keep `pr_number`/`pr_url` locals; drop only the `replace()` enrichment

- **Decided:** Step 2 keeps the `pr_number`/`pr_url` (and `pr_found`) locals in
  `check_branch_status.py` — they still feed the `--wait-for-pr` log lines
  (`"PR #%s found (%s). Proceeding..."` and the multiple-PR `"...Using PR #%s."`),
  which existing tests assert. The **only** thing removed is the post-hoc
  `replace(report, pr_number=…, pr_url=…)` enrichment (upstream
  `collect_branch_status` now fills those report fields).
- **Rationale:** the round-1 wording ("delete the `pr_number`/`pr_url` locals")
  would cause a NameError and break the log-line assertions.
- **Plan effect:** Step 2 HOW/TESTS reworded; the concrete test file
  `tests/cli/commands/test_check_branch_status_pr_waiting.py` named explicitly as
  the one whose enrichment assertions get revised.

### R2-3 — `--fail-on-reviews` intentionally not evaluated on the `--fix` path (option A)

- **Decided:** Option A — leave the pre-existing `--fix` code path as-is. It
  returns 0/1 before the review-gate `_exit_code` is evaluated, so
  `--fail-on-reviews` is not applied when `--fix` resolves CI. Out of scope, KISS.
- **Plan effect:** Step 2 documents this as a known limitation (in the step text
  and the `docs/cli-reference.md` docs task); no code change to alter the
  behaviour.
