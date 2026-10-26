# Implementation review log 2 — #1286

Supervisor-driven review of create-pr rebase / mergeability / CI wait / PR description refresh.
Previous run: `implementation_review_log_1.md` (push_failed handling, fixed in 60d8eef).

## Round 1 — 2026-10-26
**Findings**:
- 60d8eef push_failed fix verified correct in phase A and phase B (HEAD reset, expected_sha, refresh skipped).
- low: `_reset_hard` result ignored on push_failed path (pre_creation.py, post_creation.py).
- low (DRY): new `_reset_hard` in `workflow_steps/rebase.py` duplicates the one in `workflows/rebase.py`.
- low: fix-ci refresh runs after LLM timeout, may add ~5 min before the failure label.
- low: `_poll_mergeable_state` may read a stale `dirty` right after force-push.
**Decisions**:
- `_reset_hard` result: accept only a warning, if not already logged → it already logs failures; no change.
- DRY duplicate: accept — duplication introduced by this PR.
- fix-ci refresh after timeout: skip — issue explicitly requires refresh on every outcome incl. LLM failure.
- stale `dirty`: skip — shared pre-existing behaviour of fix-conflict.
**Changes**: `workflows/rebase.py` imports `_reset_hard` from `workflow_steps/rebase.py` (duplicate removed; failures now logged); `tests/workflows/rebase/test_git_helpers.py` import updated.
**Status**: committed

## Round 2 — 2026-10-26
**Findings**:
- No critical/medium issues; acceptance criteria and label table verified; f7ef320 no regression.
- (branch status) CI `file-size` fails: `tests/workflow_steps/test_rebase.py` 771 lines > 750.
- low: stale docstring in `tests/workflows/rebase/test_git_helpers.py` lists `_reset_hard` under `workflows/rebase.py`.
- low: `workflows/rebase.py` callers ignore `_reset_hard` bool and log "pre-rebase state restored" even on failure.
- low (DRY): rebase-then-reset-on-push-failure pattern repeated in `pre_creation.py` and `post_creation.py`.
**Decisions**:
- file-size: accept — CI blocker caused by this branch; split, no allowlist.
- stale docstring: accept — trivial, introduced by f7ef320.
- misleading "restored" log: accept — direct consequence of the dedup, bounded.
- DRY helper: skip — ~3 lines per site, a helper adds indirection (KISS).
**Changes**: `_poll_mergeable_state` tests moved to new `tests/workflow_steps/test_rebase_poll_mergeable.py`; docstring fixed; `workflows/rebase.py` appends `_RESTORED_NOTE` only when the reset succeeds.
**Status**: committed

## Round 3 — 2026-10-26
**Findings**:
- No regressions in bb59e13; no critical/medium issues; no file over 750 lines.
- low: no test asserts the restored vs not-restored log wording (`_RESTORED_NOTE`).
**Decisions**:
- log-wording test: skip — tests log text, not behaviour (test behaviour, not implementation).
**Changes**: none
**Status**: no changes needed

## Final Status
- Rounds: 3 (code changes in rounds 1–2, none in round 3).
- Commits: f7ef320 (`_reset_hard` dedup), bb59e13 (restored-log fix + test_rebase.py split under 750 lines), plus vulture whitelist for create-pr autouse fixtures.
- lint-imports: 19 contracts kept. vulture: clean after whitelisting autouse fixtures.
- Open: branch is behind `main`; earlier rebase hit conflicts in `docs/processes-prompts/development-process.md` and `tests/test_module_integration.py` — `/rebase` needed before merge.
