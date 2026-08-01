# Implementation Review Log — Issue #1068 (run 2)

Branch: `1068-branch-status-read-pr-review-feedback-via-dedup-onto-mcp-workspace-implementation`

Scope: shim `checks/branch_status.py` onto `mcp_workspace.checks.*`, CLI `--fail-on-reviews`
+ exit-code contract (2 → 1 → 0), review-workflow PR-feedback threading (implementation lane
only, gated by `ReviewConfig.thread_pr_feedback`).

Reference docs: GitHub issue #1068, `pr_info/steps/summary.md`, `pr_info/steps/Decisions.md`,
epic #1063, `pr_info/implementation_review_log_1.md` (run 1 — converged after 5 rounds).

Run 1 ended clean; since then the branch gained only `f46b1fa` (the run-1 log) and `bc1731c`
(gitignore for the `mcp-coder verify` artifact). This run re-reviews the full implementation
diff against `main`.

## Round 1 — 2026-08-01

**Findings**: no critical issues. The reviewer re-verified the whole contract against the
code and the installed upstream — `_exit_code` table (incl. undeterminable-over-blocking),
shim re-export surface (`collect_pr_feedback` absent, `create_empty_report` retained,
`CIStatus`/`GITHUB_TOKEN_HINT` from `branch_status_rendering`), no dangling references to the
deleted fork or `ci_log_parser`, `format_for_*(fail_on_reviews=…)` signature-checked via
`autospec`, plan lane making no GitHub call, both feed targets None-guarded, and the
round-2/3 undeterminable guard and 5-backtick fence still holding. Two suggestions:

1. *(test gap)* `check_branch_status.py:355` — the `--fail-on-reviews` → exit-code wiring had
   no end-to-end guard. Every CLI-level test used a `PASSED` report with clean feedback, so
   mutating the real call site to `_exit_code(report, False)` — silently disabling the gate
   for users — would not have failed a single test. The one genuinely new user-visible
   behaviour of Step 2 was unprotected.
2. *(Boy Scout)* `.large-files-allowlist` — the entry for `tests/checks/test_branch_status.py`
   went stale in this diff (2092 → 47 lines); `checks/file_sizes.py` detects and reports it.

**Decisions**:
- 1 — **Accept**. A gate that can be removed without a red test is untested behaviour, and
  this is the feature's headline user-visible change.
- 2 — **Accept**. Stale state created by this diff; one-line deletion.
- **Skipped, out of scope** (carried over from run 1, not re-litigated): branch behind
  `origin/main`, and the `TaskTrackerStatus` duplication vs upstream (separate issue).

**Changes**:
- `tests/cli/commands/test_check_branch_status_exit_code.py` — new
  `TestFailOnReviewsEndToEnd` driving the real `execute_check_branch_status` with
  `collect_branch_status` mocked: `pr_feedback_blocks_merge` + flag → 1, same report without
  the flag → 0, `pr_feedback_undeterminable` + flag → 2. Reuses the file's `_report()` helper.
- `.large-files-allowlist` — stale entry removed (18 allowlisted files, no stale warning).

Deliberately not done: a `--fix`-path gating case (that path returns before the review gate
by Decision R2-3), and cross-module reuse of `_make_base_args` (fragile test coupling).

**Verification**: pylint, mypy, ruff, black/isort clean; pytest 4724 passed / 2 skipped.

**Status**: committed.

## Round 2 — 2026-08-01

**Findings**: none. Critical issues: none; suggestions: none clearing the bar.

The reviewer did not merely read the round-1 tests — it **mutation-probed** them. With the
real call site at `check_branch_status.py:355` replaced by `_exit_code(report, False)` (the
exact regression the new tests exist to catch):

```
FAIL (mutation caught): test_blocking_reviews_exit_1_when_gated
PASS (mutation survived): test_blocking_reviews_exit_0_when_informational   <- control, correct
FAIL (mutation caught): test_undeterminable_reviews_exit_2_when_gated
```

Both positive tests genuinely die on broken wiring; the third is the over-eager-gating control
and correctly survives. It further confirmed the mocking does not short-circuit the path under
test (`ci_timeout=0` short-circuits `get_github_token()` before any network call;
`wait_for_pr=False` / `fix=0` route straight to line 355 through the real
`format_for_human(fail_on_reviews=…)` render), and that the exit-2 case comes from the gate
rather than the outer `except → return 2` (under the mutation it returned 0, not 2).

Re-verified and holding: shim surface vs the Decisions table (`collect_pr_feedback` has zero
references repo-wide outside the shim docstring and its absence-assertion); no dangling
references to the deleted fork (`truncate_ci_details`, `ci_log_parser` — zero hits);
`_exit_code` vs the issue's table incl. 2-over-1 precedence; `docs/cli-reference.md` matching
implemented behaviour and documenting the `--fix` limitation (R2-3); plan lane making no
GitHub call; both feed targets None-guarded; the round-2 `CIStatus.UNKNOWN` widening and the
round-3 5-backtick fence intact and covered. `.large-files-allowlist` now reports 18 files
with no stale-entry warning.

Considered and correctly not raised: items already decided by prior passes (fence
escapability, `pr_number`/`pr_url` locals, `create_empty_report` retention, `--fix` gating,
`_make_base_args` reuse), and `core.py` exceeding the 600-line threshold — pre-existing (641
lines on `main`) and not a gate this diff broke.

**Decisions**: n/a — no findings.

**Changes**: none.

**Status**: no changes needed — review loop converged.

## Final Status

**Rounds run**: 2 (round 1 produced changes; round 2 clean).

**Commits produced on this branch by run 2**:
- `28420fb` — `test(cli): cover --fail-on-reviews exit-code wiring end to end`

**Substance of run 2**: no correctness defects. Run 1 had already found and fixed the two real
ones (the undeterminable-feedback signal that could not fire on total collection failure, and
the closable data fence around untrusted PR comment text). Run 2's contribution is a genuine
test-coverage gap closed: the `--fail-on-reviews` gate — the feature's headline user-visible
behaviour — could have been silently removed from the real call site without turning a single
test red. That is now mutation-verified as guarded. Plus one stale `.large-files-allowlist`
entry removed.

**Final quality gates** (supervisor, after convergence):
- vulture — no output
- import-linter — **21 contracts kept, 0 broken**
- pylint, mypy (strict), ruff, black/isort — pass; pytest 4724 passed / 2 skipped

**Contract conformance**: exit-code precedence 2 → 1 → 0 matches the issue table; shim
re-export surface matches the Decisions table (`collect_pr_feedback` absent,
`create_empty_report` retained); plan lane makes no GitHub call; no dead code left from the
deleted fork.

**Open items for the user** (outside this review's scope):
- Branch is **1 commit behind `origin/main`** (`1085c11 feat(icoder): langchain permission
  enforcement gateway (#1103)`) — needs a rebase before merge.
- **No PR exists yet** for this branch. The tracker's `PR review feedback addressed` item is
  therefore left unticked — there is no PR feedback to address, and ticking it would record
  something that was never verified.
- `mcp_coder.workflow_utils.task_tracker.TaskTrackerStatus` duplicates the upstream enum, and
  several tests import the upstream one directly, bypassing the one-door shim convention.
  Worth a separate issue (carried over from run 1).
