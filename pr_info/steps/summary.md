# Summary — #1239: fix-conflict must always leave status-72

## Problem

`run_fix_conflict_workflow` (`src/mcp_coder/workflows/fix_conflict/core.py`) leaves the
issue at `status-72:fixing-merge-conflict` when the polled `mergeable_state` is `None`
(no open PR) or still `"unknown"` after the 30 s poll. Nothing re-evaluates `status-72`, so
the Jenkins watchdog line (`gh-tool set-status status-73 ... --from-status status-72 --force`)
moves the issue to the crash label `status-73` without a comment. The existing `dirty` →
`status-74` path also posts no comment, although the rebase reason and the conflicting
files are known.

## Fix: every handled outcome sets the final label in-process

| Polled state | Rebase outcome | Final label | Comment |
|---|---|---|---|
| `dirty` | any | `status-74:pr-merge-conflict` | yes — Verdict: still conflicting |
| other settled state (`clean`, `blocked`, `unstable`, …) | any | `status-10:pr-created` | none |
| `"unknown"` after cap | `outcome.ok` | `status-10:pr-created` | none — INFO log only |
| `"unknown"` after cap | not ok | `status-74:pr-merge-conflict` | yes — Verdict: mergeable state unknown, rebase did not complete |
| `None` (no open PR) | any | `status-74:pr-merge-conflict` | yes — Verdict: no open PR found for branch |

Unchanged: `run_guarded` crash net (→ `status-73` + "Crashed" comment), the early
`branch is None` → `return 1`, exit code 0 on all handled outcomes, the watchdog line in
`command_templates.py`, and `labels.json`.

## Architectural / design changes

- **Verdict first, one call site.** `body()` maps `(state, outcome)` to an optional verdict
  string. A verdict → one call to the new `_fail` helper (`status-74` + comment); no
  verdict → `update_workflow_label(..., "fixing_merge_conflict", "pr_created")`. There is no
  longer any path that leaves the label at `fixing_merge_conflict`, so the watchdog only
  fires on a real crash.
- **New private helper `_fail`** modelled on fix-ci's `_fail` (`workflows/fix_ci/core.py`):
  `build_failure_comment(kind="Failed")` → `handle_workflow_failure(category="pr_merge_conflict", ...)`.
  `handle_workflow_failure` sets the label and posts the comment (issue number from the
  branch), so `status-74` paths do not call `update_workflow_label` separately.
- **Comment fields** reuse the shared builder (`workflow_utils/failure_handling.py`):
  `Verdict`, `Reason` (only when the rebase failed), `Base`, and `Likely conflicting files` /
  `Uncommitted files` when `outcome.files` is non-empty. `None` values are dropped by the
  builder; ordering comes from `FIELD_ORDER`. `Branch`/`Build` are added by the builder.
- **Rebase-ok gate on `unknown`** prevents a 10 → 71 → 72 → 10 dispatch loop when the rebase
  changed nothing on GitHub. `unknown` + ok is safe at `status-10` because the detection
  re-checks `dirty` on every `status-10` poll.
- No new modules, CLI flags, labels or dependencies.

## Files modified

| File | Change |
|---|---|
| `src/mcp_coder/workflows/fix_conflict/core.py` | add `_fail`, rewrite outcome branching in `body()`, docstring + log message |
| `tests/workflows/fix_conflict/test_core.py` | extend `_patch_all`; parametrized `status-74` and `status-10` tests replace the dirty/clean/unknown/no-PR tests |
| `docs/cli-reference.md` | `fix-conflict` description: outcome list instead of "stays at status-72" |
| `docs/processes-prompts/development-process.md` | §10 tree branches; `status-74` row in human-action table |
| `docs/getting-started/label-setup.md` | `status-74` description |

No files are created (besides these plan files).

## Steps

1. `step_1.md` — code + tests: in-process final label for every outcome, `status-74` comments.
2. `step_2.md` — docs: describe the new outcomes and reword `status-74`.

## Outside the plan

After merge, post a pointer comment on #1212 referring to #1239 for the corrected `unknown`
handling (body of #1212 unchanged). This is a manual GitHub action, not a commit.
