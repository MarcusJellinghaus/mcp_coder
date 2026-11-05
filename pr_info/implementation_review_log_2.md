# Implementation review log 2 — Issue #1382

Supervised review of the rebase-then-force-with-lease fix. Log 1 was an automated run that handed off on a rebase conflict.

## Round 1 — 2026-11-04
**Findings**:
- Branch is 1 commit behind `origin/main` (#1383); merge-tree shows conflicts in `mcp_workspace_git.py`, `workflow_steps/rebase.py`, `fix_conflict/core.py`, `workflows/rebase.py`
- After rebase, `rebase_with_llm_fallback` would report a `branch_moved` stop as `conflict` (read from `origin/main`, not run)
- After rebase, bare `return 2` in `run_rebase_workflow` no longer fits its `RebaseRunResult` return type (read only)
- After rebase, new tests in `test_workflow_branch_moved.py`, `fix_conflict/test_core.py`, `test_post_creation.py` break against main's signatures and labels (read only)
- After rebase, create-pr post-creation on `branch_moved` with a dirty PR gets status-71, which appears to re-dispatch fix-conflict, while the new comment tells a human to re-run (read only)
- `/rebase` skill treats any `rev_parse` error as an absent ref
- `/rebase` skill leaves a `merge_base` error to Abort Rule 1, with no reset command at the second check
- Literal `origin/<branch>` in the shared reason text
- `test_failed_post_changes_nothing` asserts an exit code that holds only because the label function is mocked
- `test_branch_moved_rebase_outcome_continues_workflow` passes without the fix

**Decisions**:
- Rebase and the three post-rebase blockers: escalated to the user. They need a conflict-resolving rebase and force-push, and cannot be implemented or run before it
- status-71 comment wording: escalated, it departs from what the issue assumed
- `rev_parse` and `merge_base` handling in the skill: accept, real gaps in the guard
- Literal `origin/<branch>`: skip, matches the issue wording and the comment's Branch field gives the name
- `test_failed_post_changes_nothing`: skip for now, this file is rewritten during the rebase
- `test_branch_moved_rebase_outcome_continues_workflow`: skip, pins behaviour the issue asks for; the warning is covered in `test_rebase_branch_moved.py`

**Changes**: `.claude/skills/rebase/SKILL.md`: skip the check only on `fatal: Needed a single revision`; any other `rev_parse` error and any `merge_base` error is a stop, with the reset command printed after the rebase.
**Status**: committed; rebase blockers open

## Rebase — 2026-11-04
**Changes**: `/rebase` run at the user's request, onto `origin/main` (`c29c0d8`); conflicts resolved in the four files above. `ad38e03` routes branch-check stops through `rebase_with_llm_fallback` (`RebaseRunResult.branch_check`) and adapts the tests to main.
**Status**: force-pushed with the user's confirmation (`81e9a0c..ad38e03`). status-71 comment wording: the user chose to leave it unchanged.

## Round 2 — 2026-11-04
**Findings**:
- `_post_branch_moved_comment` in fix-conflict says `Stage: Mechanical rebase` after an LLM session and loses `llm_detail`, including a failed restore
- No real-git test goes through `rebase_with_llm_fallback`
- `rebase_automated.py` and `docs/cli-reference.md` describe only a plain push after the fallback; "LLM rebase succeeded" is reported after a no-op
- `run_rebase_workflow` Returns docstring omits `branch_check`
- Branch is 1 commit behind `origin/main` (#1384); clean rebase expected (read only)

**Decisions**:
- Fix-conflict comment: accept, a human must learn the checkout was not restored
- Real-git fallback tests: accept, the mapping is otherwise covered only by mocks
- Fallback wording: skip, pre-existing
- Docstring: accept
- #1384 rebase: reported to the user at the end; a force-push needs their confirmation

**Changes**: fix-conflict's settled-state comment takes `outcome`, adds the `LLM rebase` field and uses Stage `Rebase`; `TestBranchMovedRealGit` covers two real-git paths through `rebase_with_llm_fallback` (both fail with the mapping removed); `run_rebase_workflow` docstring mentions `branch_check`.
**Status**: committed

## Round 3 — 2026-11-04
**Findings**:
- #1376 merged to main (`4b8f320`, `dea9aea`), so this branch merges second and must update the failure comment in `workflow_steps/commit.py`, which warns that a re-run can overwrite the new commit
- Rebasing conflicts in `review/handoff.py`: both sides import a different `BRANCH_MOVED_NEXT_STEP`, and `handoff.py` needs both

**Decisions**:
- Failure comment: accept, the issue and step 5 assign it to whichever merges second
- `handoff.py`: accept, alias or rename so each path keeps its own text

**Changes**: rebased onto `origin/main` (`dea9aea`); `handoff.py` aliases the rebase constant as `REBASE_BRANCH_MOVED_NEXT_STEP`; `commit.py` next step reworded and its #1382 note removed; both constants pinned in review tests. `test_full_workflow_success` failed once in a parallel run, then passed alone and in a full re-run; cause not established.
**Status**: committed; force-pushed with the user's confirmation (`f23681b..3ca0bd2`)

## Round 4 — 2026-11-05
**Findings**:
- No findings on this branch
- `test_full_workflow_success` makes a real Claude call in the fast suite: it does not patch `prompt_llm` in `implement/finalisation.py`, and an exception from that call reproduces `assert 1 == 0`. The exception in the failed run was not captured.

**Decisions**:
- Test flake: skip, pre-existing. The branch does not touch the test or `workflows/implement/`. Reported to the user.

**Changes**: none
**Status**: no changes needed

## Final Status
- Rounds: 4, plus two rebases onto `origin/main`, each force-pushed with the user's confirmation. Round 4 produced no code changes.
- vulture clean; lint-imports 19 kept, 0 broken.
- Open: the pre-existing `test_full_workflow_success` flake above.
