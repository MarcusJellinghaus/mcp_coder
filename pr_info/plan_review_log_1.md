# review-plan review log 1

## Round 1 — 2026-10-26
**Findings**:
pr_info/steps/summary.md:12 — medium — Allowed edits are narrower than the issue's. The issue's "How to move" steps 3–4 and its fallback for `NameError`/`ImportError` at collection allow a different grouping or call order, `move_module`, undoing with `move_symbol`, and as a last resort hand-moving whole top-level statements. The plan bans all of these ("Never move code by hand", block on any failure), so a misplaced symbol blocks a case the issue meant to recover from. Add the issue's recovery path to the move procedure (lines 69–74).
pr_info/steps/step_4.md:56 — medium — The compact-diff allowlist leaves out "moved-block preview/summary lines", which the issue's Verification lists as allowed. The compact diff always prints these lines for moved blocks, so a strict reading flags a correct diff as blocked. Add that item.
pr_info/steps/step_4.md:49 — low — "or whatever step 1 recorded" contradicts `pr_info/steps/step_1.md:21`, which stops on any number other than 6463 and never says where to record the values for a later step. Either drop the alternative here or say in step 1 where the recorded numbers go.
pr_info/steps/summary.md:83 — low — The standard checks don't say what scope pytest runs on (whole fast-unit suite or only the affected files). The issue's Verification wants both: the full unit run with `-n auto`, and the five files run directly. Say which applies per step.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/summary.md (move procedure, lines 69–74), replace the blanket 'Never move code by hand' and 'block on any failure' rules with the issue's recovery path. On NameError/ImportError at collection or a misplaced symbol, first try a different grouping or call order. If that fails, use move_module, or undo with move_symbol. As a last resort, hand-move whole top-level statements. Block only after all of these fail.", "In pr_info/steps/step_4.md (~line 56), add 'moved-block preview/summary lines' to the list of allowed compact-diff output, as the issue's Verification section allows.", "Resolve the contradiction between pr_info/steps/step_4.md:49 and pr_info/steps/step_1.md:21. Since step 1 stops on any count other than 6463, remove 'or whatever step 1 recorded' from step_4.md and state 6463 as the expected value.", "In pr_info/steps/summary.md (~line 83, standard checks), give the pytest scope for each step. Every step runs the full fast-unit suite with -n auto, and the five affected test files are also run directly, matching the issue's Verification section."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-26
**Findings**:
pr_info/steps/step_4.md:54 — high — The compact-diff check runs against the base branch with no pathspec, so it will also show the branch's `pr_info/` files (`steps/*`, `TASK_TRACKER.md`, `plan_review_log_*.md`). None of these are on the allowed list in lines 56–60, so read strictly, a correct split gets written to `.blocked.txt` at the last step. Fix: limit the diff to `tests/workflows/implement/` and `.large-files-allowlist` with `pathspec`, or add `pr_info/` to the allowed list.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_4.md (~line 54), scope the compact-diff check against the base branch with a pathspec limited to `tests/workflows/implement/` and `.large-files-allowlist`. The branch's own `pr_info/` files (steps, TASK_TRACKER.md, plan_review_log_*.md) are then not counted as disallowed changes, and a correct split no longer ends up in `.blocked.txt`."], escalate_reason=None)
**Changes**:
applied
