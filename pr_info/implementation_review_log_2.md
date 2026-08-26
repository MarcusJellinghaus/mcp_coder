# Implementation review log 2 — issue #1113

Continues `implementation_review_log_1.md`, which recorded rounds 1-3. Round numbering
carries on from there rather than restarting, so the history reads as one sequence.

State at the start of this run:

- Steps 1-7 implemented, committed, and rebased onto `origin/main`. No rebase pending.
- Requirement 1's manual marker probes were executed on 2026-08-26 and recorded in
  `pr_info/TASK_TRACKER.md` (commit `6ac641e`). The pre-fix install reproduced the bug; the
  branch source shows the marker absent and the repo's own rules in effect. Rounds 1-3 each
  reported this evidence as missing — that finding is now closed.
- The live post-fix run surfaced one candidate defect for this round: the context report
  named the user-level `~/.claude/CLAUDE.md` and warned it lies outside `project_dir`,
  although the project's own rules did arrive. `steps/summary.md` §5 puts user-level files
  out of the report's scope.

## Round 4 — 2026-08-26

**Findings**

- `cli/utils.py:434-442` — medium — the outside-`project_dir` warning fires once per hit
  outside `project_dir`. Because the walk collects hits at every ancestor level and every
  ancestor is outside by definition, it fires on almost every run. Observed live: a healthy
  run that found and used the project's own `.claude/CLAUDE.md` still warned "the driven
  project's rules may not reach the agent" about the user-level `~/.claude/CLAUDE.md`.
- `cli/utils.py:366`, `docs/architecture/architecture.md`, `steps/summary.md` §5 — low —
  all three state the walk excludes user-level `~/.claude/CLAUDE.md`. It does not: the file
  is reached whenever the project sits under the home directory.
- `cli/commands/check_branch_status.py:191-199` — low — the comment justifying the resolver
  hoist also documents code that did not change.
- Branch is one commit behind `origin/main` (#1136).

**Decisions**

- **Accept** the warning fix. The diagnosis is a predicate/scope mismatch, not a wording
  problem: requirement 5's per-hit predicate was written for the nearest-level walk the
  issue specified, where a project holding its own `CLAUDE.md` could never trigger it. Round
  1 changed the walk to all levels — correctly, Claude loads the whole chain — and left the
  predicate. Narrowing the walk was rejected as the weaker option: it would patch only the
  home case, while a workspace or monorepo parent `CLAUDE.md` above a checkout would still
  misfire.
- **Accept** the three text corrections. The all-levels walk is the better behaviour, so the
  text is what needs amending — the same resolution rounds 2 and 3 reached for the
  nearest-level deviation.
- **Accept** the comment trim. Bounded, and the knowledge base prefers readable code to
  commentary.
- **Defer** the rebase to the end of the review loop.
- Round 3's dismissed finding about the warning text is reopened on new evidence: the live
  probe shows it is not hypothetical, and the fix is a predicate change rather than a
  rewording.

**Changes**

`report_context_root` now warns once per run when no reported hit lies inside `project_dir`
— exactly the drift #1113 exists to catch — with wording that also covers a project having
no `CLAUDE.md` of its own. `is_outside_project_dir` remains the single definition of
"outside"; `verify` keeps per-hit outside-ness as a row annotation rather than a warning
gate. One test inverted and one added, both written first and confirmed failing against the
old code, both using the stubbed finder so no assertion depends on the machine having a
user-level `CLAUDE.md`. Four stale user-level scope claims corrected (a fourth was found in
the `_CONTEXT_LABEL` comment). Hoist comment cut from eight lines to two.

**Status**: committed. Gates: pylint clean, pytest 5113 passed / 2 skipped, mypy clean,
import-linter 21/21 kept.

## Round 5 — 2026-08-26

**Findings**

- `docs/environments/environments.md:146-147` — low — still describes the retired per-hit
  predicate ("warning when one lies outside `project_dir`"). A reader would expect a warning
  on a normal healthy run and read its absence as the reporting being broken. Round 4's
  correction sweep missed this fourth site.
- Nothing else. The reviewer scrutinised `ced93a8` specifically on the three edge cases it
  introduced and found no defects: with `project_dir=None` every hit is "not outside", so
  `all(...)` is `False` and nothing warns — correct, since with no anchor there is nothing to
  be outside of; the "none found" early return sits *before* the predicate, which is
  load-bearing because `all([])` is `True` and an empty walk would otherwise warn while
  naming an empty file list; and when `execution_dir` sits above `project_dir` the project's
  own file is never reached and the warning correctly fires — the case a nearest-level walk
  would have missed.
- Findings dismissed in rounds 1-4 were re-examined and not re-raised; no new evidence
  against any of them.

**Decisions**

- **Accept** the doc correction, and extend it to a repo-wide sweep for the same two stale
  claims (the retired per-hit predicate, and the false "walk excludes user-level
  `~/.claude/CLAUDE.md`"). The round-4 sweep having missed a site once is reason to verify
  rather than assume the rest are clean.

**Changes**

`environments.md` now states the current predicate plus why individual outside hits are
normal. The sweep found one further site: `tests/cli/test_utils_context_root.py:179`, whose
name `test_report_warns_when_hit_is_outside_project_dir` asserted the retired per-hit rule
and contradicted its own sibling three tests later — renamed to
`test_report_warns_when_the_only_hit_is_outside_project_dir` with a docstring stating the
warning fires because no hit is inside. Nothing else stale: `utils.py`'s docstrings,
`architecture.md:167-174` and `verify.py:380-382` were already correct, and
`test_verify_prompts_context.py:115`'s `test_hit_outside_project_dir_warns` is accurate
because verify genuinely does still mark each outside row. The `@import` caveat is intact at
all three sites.

**Status**: committed. Gates: pylint clean, pytest 5113 passed / 2 skipped, mypy clean,
import-linter 21/21 kept.
