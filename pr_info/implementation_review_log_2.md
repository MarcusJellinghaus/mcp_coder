# Implementation review log 2 — issue #1146

Supervisor-driven review of `_exit_code` linked-branch terms (shim re-export, exit-code ladder, docs, `implementation_approve` skill wording, tests). Follows log 1 (3 rounds, ended on rebase-needed).

## Round 1 — 2026-10-21
**Findings**:
- `docs/cli-reference.md:781` — note says closing-PR-only link is `NOT_LINKED` → exit 1; upstream now has `LINKED_VIA_PR` (non-blocking, exit 0).
- `tests/cli/commands/test_check_branch_status_exit_code.py` — state table lacks `LINKED_VIA_PR`.
- `pr_info/steps/summary.md` still lists six states.
- Branch behind `origin/main`, needs rebase.

**Decisions**:
- Doc note: accept (critical) — supervisor confirmed `LINKED_VIA_PR` in installed `mcp_workspace` and the reference project; the round-2 fix of log 1 predates it.
- Test row: accept — covers every upstream state, pins the non-blocking exit code.
- summary.md: skip — pr_info/ is deleted later.
- Rebase: handled at branch-status check.

**Changes**: doc note rewritten (linked-branches list wins; matching closing PR → `LINKED_VIA_PR`/0; non-matching closing PRs → `MISMATCH`/1; none → `NOT_LINKED`/1); `(LINKED_VIA_PR, 0)` added to the parametrize table. pylint/mypy/pytest (5808 passed) clean.
**Status**: committed
