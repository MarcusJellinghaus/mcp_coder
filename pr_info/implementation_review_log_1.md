# review-implementation review log 1

## Round 1 — 2026-09-27
**Findings**:
I'll gather context first.`src/mcp_coder/workflows/review/core.py:141` — high — the top-of-loop flush creates a commit that a following `dismiss` round force-pushes in `_attempt_rebase_and_push` immediately before the CI gate; `_poll_for_ci_completion` correlates by branch-latest run (`get_latest_ci_status(branch)` → `runs_paged[0]`), not by local HEAD SHA, so it can return the *previous* commit's completed green at once, after which `check_ci_proven_gate`'s fresh status read observes the newly-queued run as PENDING and returns `ci_unknown` — a terminal failure on a round that previously pushed nothing (a no-op-rebase dismiss round). summary.md accounts only for "one extra CI cycle", not for this stale-green/PENDING race.

`src/mcp_coder/workflows/review/handoff.py:171` — medium — `commit_staged_files` commits the whole index, so anything already staged rides along; the docstring's guarantee at line 159-160 ("commit *only* this path … an arbitrarily dirty tree can never ride along under ``message``") is stronger than the code delivers.

`src/mcp_coder/workflows/review/handoff.py:219` — medium — `_route_to_human` still flushes with `commit_all_changes` + push, so the dirty tree that step 2's new tripwire refused to rebase over is auto-committed under "Add review round log" and pushed on the very handoff the tripwire triggers, defeating the issue's "fail loudly instead of repairing silently" intent for that path.

`src/mcp_coder/workflow_steps/rebase.py:66` — low — the warning hardcodes a review-lane cause ("likely a leftover uncommitted write") in code shared with the `implement` workflow, where dirt at that point has a different origin (e.g. a regenerated `uv.lock` that `check_git_clean` tolerates).

`tests/workflows/review/test_core.py:92` — low — the duplicate `env` fixture was not updated alongside `tests/workflows/review/conftest.py`, so plan-lane tests run the real `stage_specific_files` against a non-repo `tmp_path`; the top-of-loop flush is silently a no-op there and the new invariant is untested in that lane.

`src/mcp_coder/workflows/review/core.py:202` — low — on the reviewer/supervisor `_fail` sites (also 217, 251, 262) the previous round's flush commit is never pushed, leaving the workspace branch ahead of origin with a commit no terminal path delivers.
**Decisions**:
Verdict(decision='tasks', tasks=["src/mcp_coder/workflows/review/core.py:141 — fix the stale-green race between the top-of-loop round-log flush and the CI gate: after _attempt_rebase_and_push pushes, correlate CI polling with the pushed local HEAD SHA rather than with the branch-latest run (get_latest_ci_status(branch) → runs_paged[0]), so _poll_for_ci_completion cannot return the previous commit's completed green and leave check_ci_proven_gate observing the newly-queued run as PENDING → ci_unknown. Add a regression test covering the no-op-rebase dismiss round that pushes only the flush commit: previous run green, new run queued, gate must not terminally fail. Update summary.md so it describes this race and its resolution, not just 'one extra CI cycle'.", "src/mcp_coder/workflows/review/handoff.py:171 — make the code match the docstring guarantee at lines 159-160, or weaken the docstring. Preferred: commit only the round-log path (pathspec-scoped commit) so pre-staged entries in the index cannot ride along under the 'Add review round log' message. Add a test that stages an unrelated file first and asserts the resulting commit touches only the round-log path.", 'src/mcp_coder/workflows/review/handoff.py:219 — stop _route_to_human from silently repairing a dirty tree: replace the commit_all_changes + push flush with a round-log-only commit (same scoped mechanism as the fix above), so the dirt the step-2 rebase tripwire refused to rebase over is not auto-committed and pushed on the very handoff the tripwire triggers. Add a test asserting that unrelated dirty files remain uncommitted after _route_to_human.', "src/mcp_coder/workflow_steps/rebase.py:66 — reword the dirty-tree warning so it does not hardcode the review-lane cause ('likely a leftover uncommitted write'); state the observed condition and the named cause generically, since the same code runs in the implement workflow where the dirt has a different origin.", 'tests/workflows/review/test_core.py:92 — update the duplicate `env` fixture to match tests/workflows/review/conftest.py so the plan lane no longer runs the real stage_specific_files against a non-repo tmp_path, then add a test asserting the top-of-loop flush actually happens in that lane (currently a silent no-op, leaving the new invariant untested there). Prefer removing the duplicate in favour of the conftest fixture if nothing in the module needs the local variant.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-09-27
**Findings**:
I'll gather context first.`src/mcp_coder/workflows/review/handoff.py:198` — medium — the `only=` flush refuses outright when the index holds any unrelated staged entry, so on the rebase handoff reached *because* the tree is dirty with **staged** changes, `_route_to_human` now lands no round-log entry at all (before this branch, `commit_all_changes` always landed it); the handoff comment is posted with nothing recorded in the committed review log.

`src/mcp_coder/workflow_steps/ci.py:312` — medium — when `expected_sha` never appears (no workflow triggers for that commit, or another actor pushes past it), `is_other_commit` keeps the poll looping for the full `CI_MAX_POLL_ATTEMPTS` (12.5 min) before the graceful `(None, True)`; without `expected_sha` the same call returned the newest run immediately, so this is a new worst-case stall on a code path shared with `implement`.

`tests/workflow_steps/test_ci.py:192` — low — no test covers the new `is_other_commit` cap-exhaustion branch (`CI_TIMEOUT: No CI run appeared for …` → `(None, True)`); the four added tests all exercise the match-eventually path.

`src/mcp_coder/workflows/review/core.py:186` — low — the loop-entry flush commit is never pushed on the reviewer/supervisor `_fail` sites (also 201, 235, 246), leaving the workspace branch ahead of origin with a commit no terminal path delivers (carried over from round 1; accepted in `pr_info/steps/summary.md`).
**Decisions**:
Verdict(decision='tasks', tasks=['src/mcp_coder/workflows/review/handoff.py:198 — restore the guarantee that _route_to_human always lands a round-log entry. The `only=` flush must not refuse outright when the index holds unrelated staged entries: on the rebase handoff (reached precisely because the tree is dirty, possibly with staged changes) the round log must still be committed with only the round-log path included, leaving the unrelated staged entries uncommitted in the index. Add a test that stages an unrelated file, routes to human, and asserts the round-log entry is present in the committed log while the unrelated file is still uncommitted.', "src/mcp_coder/workflow_steps/ci.py:312 — remove the new worst-case stall: when `expected_sha` never appears (no workflow triggered for that commit, or another actor pushed past it), do not keep looping `is_other_commit` for the full CI_MAX_POLL_ATTEMPTS (~12.5 min) before returning (None, True). Bound that wait with a short dedicated budget for 'no run yet for expected_sha' and return the graceful (None, True) once it expires, so the shared `implement` path is not penalised.", "tests/workflow_steps/test_ci.py:192 — add a test for the `is_other_commit` exhaustion branch: expected_sha never appears, assert the CI_TIMEOUT log ('No CI run appeared for …') and the (None, True) return, and assert the bounded attempt count from the fix above rather than the full CI_MAX_POLL_ATTEMPTS."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-09-27
**Findings**:
I'll gather context first.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
