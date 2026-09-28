# Implementation Review Log 2 — Issue #1158

Supervised review of the implementation for issue #1158
(review-implementation: successful tasks round leaves round-log write uncommitted,
breaks next round's rebase).

Run 1 (`implementation_review_log_1.md`) was the automated Jenkins run; it ended on a
rebase handoff after round 3 dismissed. This run continues the review.

## Round 1 — 2026-09-28

**Findings**:
- `src/mcp_coder/workflow_steps/ci.py:339` — low — the `expected_sha` give-up branch returns `(None, True)`, which `check_and_fix_ci` reads as "CI passed"; `check_ci_proven_gate` then correlates by branch, so a previous commit's green can still prove the flush commit green.
- `src/mcp_coder/workflows/review/handoff.py:285-300` — low — the `only=` flush stages the round log before committing it, so a failed commit leaves it staged; the new rebase tripwire refuses on staged entries, whereas the untracked first-run log it started from is something `git rebase` tolerates.
- `src/mcp_coder/workflows/review/handoff.py:212` — low — `_commit_only_path` runs `git commit` at `execute_command`'s default 120 s timeout while the `commit_staged_files` route has none, so a slow `pre-commit` hook fails one route and not the other.
- `src/mcp_coder/workflow_steps/constants.py:41` — low — the comment claims "~2 minutes max wait" for a bound that is ~105 s.
- Noted, not blocking: `core.py:186/201/235/246` leave the loop-entry flush commit local and unpushed (explicitly accepted in `summary.md`); `core.py:457` whole-tree-commits half-applied edits after a mid-fix reviewer crash (pre-existing, documented as intentional).

**Decisions**:
- `handoff.py:285-300` — **accept**. A real regression introduced by this diff: a failed flush converts a rebase that would have succeeded into a needs-human handoff. Bounded fix.
- `constants.py:41` — **accept**. One-line accuracy fix in code this diff added (Boy Scout).
- `ci.py:339` — **skip**. Unchanged in shape from before the diff and now bounded rather than unbounded; closing it means adding SHA correlation to `check_ci_proven_gate`, a separate concern from #1158.
- `handoff.py:212` — **skip**. Speculative — requires a `pre-commit` hook exceeding 120 s.
- Noted items — **skip**. Pre-existing and already accepted in the plan.

**Changes**:
- `handoff.py`: new best-effort `_unstage_path` (`git reset -q HEAD -- <path>` via the `subprocess_runner` shim, the same escape hatch `_commit_only_path` uses); `_flush_round_log` calls it when an `only=` commit fails, so unrelated staged entries are untouched.
- `constants.py`: `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` comment corrected to ~105 s, with the reason (the sleep follows each non-final attempt). `CI_MAX_POLL_ATTEMPTS` and `CI_NEW_RUN_MAX_POLL_ATTEMPTS` were checked and are accurate — their sleeps are unguarded, so those comments stand.
- `tests/workflows/review/test_handoff.py`: three tests — the reset argv is issued and the push skipped on a failed scoped commit; a failing reset only warns; and a `git_integration` test asserting the log returns to untracked with its content intact while an unrelated staged entry stays staged.

**Checks**: format clean, pylint clean, pytest 5549 passed / 2 skipped, mypy clean, `git_integration` handoff tests 2 passed.

**Status**: committed

## Round 2 — 2026-09-28

**Findings**:
- `pr_info/steps/summary.md:147` — low — stale spec: still describes the pre-fix full-`CI_MAX_POLL_ATTEMPTS` wait that round 2 of run 1 replaced with the dedicated `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` budget.
- `pr_info/steps/summary.md:265,276` — low — the files-modified table says `_flush_round_log` refuses when the index holds unrelated entries, contradicting the same document's body and the shipped pathspec-commit code; the table also omits `_commit_only_path` and `_unstage_path`.
- `tests/workflow_steps/test_ci.py:249` — low — the give-up test's docstring says "~2 minutes", the exact wording `c3f013a` corrected to ~105 s in `constants.py`.
- No findings on `handoff.py`, `core.py`, `steps.py`, `ci.py`, `rebase.py` or `mcp_workspace_git.py`.

Out of band, from `check_branch_status`: CI red on the `file-size` job — `tests/workflows/review/test_handoff.py` at 802 lines against the 750-line gate.

**Decisions**:
- `test_ci.py:249` — **accept**. Same inaccuracy just corrected in the constant, in a file that ships.
- Both `summary.md` findings — **skip**. `pr_info/` is background material deleted later in the process (`software_engineering_principles.md`, "Don't Worry About"); the staleness does not reach shipped code.
- The `file-size` failure — **fix**. Split the file rather than allowlist it: `.large-files-allowlist`'s own header records its entries as grandfathered and being reduced (issue #353).

**Changes**:
- `tests/workflows/review/test_handoff.py` reduced to 496 lines, keeping `_flush_round_log` and its commit helpers; the `_route_to_human` and `_fail` sections moved to the new `tests/workflows/review/test_handoff_route.py` (325 lines), taking the `routed` fixture with their only users so `conftest.py` is unchanged. Naming follows the directory's `test_core*.py` convention. A pure move — 27 tests before, 27 after, no assertion changed.
- `tests/workflow_steps/test_ci.py`: docstring corrected to ~105 seconds.
- Verified: `check_file_size(max_lines=750)` passes across all 857 files; `.large-files-allowlist` untouched.

**Checks**: format clean, pylint clean, pytest 5549 passed / 2 skipped, mypy clean, `git_integration` in `tests/workflows/review/` 2 passed (one per resulting file).

**Status**: committed

## Round 3 — 2026-09-28

**Findings**: NO FINDINGS

The round also verified `4dfd6f6`'s pure-move claim rather than taking it on trust: 16 + 11 = 27 tests with names identical to the 27 in the pre-split file, 19 + 21 = 40 assertions matching line-for-line in order, the only non-move edit being the module docstring, the `routed` fixture present in exactly one file, `conftest.py` untouched, and one `git_integration` test per file correctly matched to its subject.

**Decisions**: nothing to accept — no code changes this round, so the review loop ends here.

**Changes**: none.

**Status**: no changes needed

## Final Status

Three rounds in this run, two of which produced commits:

| Commit | Scope |
|--------|-------|
| `c3f013a` | `_unstage_path` — a failed `only=` scoped commit no longer leaves the round log staged; corrected `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` wait comment |
| `4dfd6f6` | Split `test_handoff.py` under the 750-line CI gate; corrected the give-up budget docstring |

**Checks at close**: pylint clean, mypy clean, pytest 5549 passed / 2 skipped, `git_integration` review tests passing, vulture no output, import-linter 21 contracts kept / 0 broken, `check_file_size` within limits across all 857 files with `.large-files-allowlist` untouched.

**Branch**: CI PASSED on `4dfd6f6`, up to date with `main` (no rebase needed), all task-tracker tasks complete, label `status-07:code-review`. No PR exists yet.

**Deliberately not fixed** (decisions recorded above and in round 1):
- The `expected_sha` give-up branch's residual stale-green exposure in `ci.py` — unchanged in shape from before this branch and now bounded rather than unbounded; closing it means adding SHA correlation to `check_ci_proven_gate`, separate from #1158.
- The 120 s `execute_command` default on `_commit_only_path` / `_unstage_path` versus no timeout on the GitPython route — only reachable via a `pre-commit` hook exceeding 120 s.
- The unpushed loop-entry flush commit on the four `_fail` sites in `core.py` — explicitly accepted in `pr_info/steps/summary.md`.
- `core.py:457`'s whole-tree commit of half-applied edits after a mid-fix reviewer crash — pre-existing and documented as intentional.
- Stale content in `pr_info/steps/summary.md` (the `expected_sha` give-up description at line 147, and the files-modified table at 265/276 still describing the refuse-on-unrelated-staged behaviour the pathspec commit replaced) — `pr_info/` is background material deleted later in the process. Worth noting if that folder's content is ever used to regenerate the issue or the PR body.

Issue #1158's own *Fix* text also still prescribes a bare `_flush_round_log(project_dir)` and an `is_working_directory_clean` check, both of which the implementation deliberately deviates from; `summary.md`'s *Deviation from the issue text* section records why. The issue may want updating to match.
