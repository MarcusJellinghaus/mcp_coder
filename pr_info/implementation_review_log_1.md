# Implementation Review Log — Issue #695

Refactor: replace bat/sh orchestration templates with thin launcher + Python `session_setup`.

Supervisor: technical lead delegating to engineer subagents.
Started: 2026-07-06

## Round 1 — 2026-07-06

**Findings** (from `/implementation_review` engineer subagent; implementation diff confirmed present, no Critical issues):
- **F1 [Accept, low]** `run_first_step` (`session_setup.py`) uses `capture_output=True` and only reads stdout; on empty session id it raises a generic error and discards the underlying `mcp-coder` stderr → debuggability regression (undercuts the refactor's core goal).
- **F2 [Skip, pre-existing]** Session restart / regenerate call site in `session_launch.py` (~L450) doesn't thread `skip_github_install`.
- **F3 [Accept, low]** `update_gitignore` short-circuits when a marker line already exists, so coordinator repos that committed the *old* gitignore block never gain the new `.vscodeclaude_session.json` entry.
- Verified PASS: env-dict assembly, flag fidelity (`--strict-mcp-config`/`--output-format session-id`/session-id/timeout), flow shapes (0/1/multi/intervention), `skip_github_install` round-trip, install.py delegation argv, UTF-8-before-banner ordering, exit-0-after-prompt, intervention warning parity. Test coverage strong (both platforms).

**Decisions**:
- F1 → **Accept**. Directly serves the refactor's stated debuggability goal.
- F2 → **Skip**. Confirmed pre-existing: this branch does not touch `session_launch.py` at all; `create_startup_script` has no such param on the restart path in `main` either. Out of scope. Flagged to user.
- F3 → **Accept**. The gap is introduced by this PR adding a new `GITIGNORE_ENTRY` line; making the updater idempotent per-line is a bounded Boy-Scout fix.

**Changes**:
- `session_setup.py::run_first_step` — on empty session id, print captured stderr to `sys.stderr` and include trimmed stderr + returncode in the `RuntimeError`.
- `workspace.py::update_gitignore` — append only the `GITIGNORE_ENTRY` pattern lines that are missing (fresh repo still gets full block; up-to-date repo unchanged byte-for-byte).
- Tests: `test_session_setup_flow.py` (stderr-surfaced test + `_FakeRun` stderr support), `test_workspace.py` (upgrade-appends + up-to-date-unchanged tests).
- Checks: pylint PASS, mypy PASS, pytest PASS (4170 passed, 2 skipped).

**Status**: changes made; commit pending.

## Round 2 — 2026-07-06

**Findings**: None. Fresh review of the updated branch. Both Round-1 fixes verified correct, complete, and tested (`run_first_step` surfaces stderr+returncode on empty session id; `update_gitignore` idempotent per-line). Broad pass over the full diff — flag fidelity, flow shapes, env assembly, install.py delegation, `skip_github_install` round-trip, banner UTF-8 ordering, exit-0-after-prompt, intervention parity — all match the retired templates and Decisions.md. Tests green (597 passed, 2 skipped), mypy + pylint clean.

**Decisions**: No accepted findings.

**Changes**: None.

**Status**: no changes needed — review loop complete.

## Post-review checks (step 8) — 2026-07-06

**vulture**: flagged `workspace.py:499 unused variable 'session_folder_path'` — the intentional signature-stability param documented in `Decisions.md`. Fixed via a targeted `vulture_whitelist.py` entry (`_.session_folder_path`).

**lint-imports**: `Subprocess Library Isolation` contract BROKEN — `session_setup.py` (and its test) import raw `subprocess`, needed for the interactive `claude` console handoff that the capture-oriented `subprocess_runner` shim cannot do. Escalated to user → approved allowlisting (mirrors the existing `mcp_verification` exemption). Added two `ignore_imports` entries to the active `subprocess_isolation` contract in `.importlinter`.

Re-ran both (supervisor): vulture clean (no output); lint-imports **19 kept, 0 broken**.

## Final Status

**Rounds run**: 2.
- Round 1 — 3 findings: F1 (step-1 stderr visibility) and F3 (idempotent gitignore) accepted & fixed; F2 (restart path doesn't thread `skip_github_install`) skipped as pre-existing/out-of-scope.
- Round 2 — no findings; both fixes verified correct and tested; broad pass clean.

**Post-review checks (step 8)**: vulture clean; lint-imports 19/19 KEPT after user-approved allowlist of `session_setup`'s subprocess import + vulture whitelist for the retained param.

**Commits produced this review**:
- `e6159a9` — Surface step-1 stderr; idempotent gitignore upgrade.
- `8d79d3a` — Allowlist `session_setup` subprocess import; vulture whitelist for retained param.
- (this log committed separately)

**Quality gates**: pylint, mypy, pytest (unit suite green), vulture, lint-imports — all passing.

**Outstanding / noted**: F2 — the session restart / regenerate call site (`session_launch.py`) does not thread `skip_github_install`. Confirmed pre-existing (this branch does not touch that file); a restarted session defaults to overrides-ON. Out of scope for #695; worth a separate follow-up if the behavior matters.

**Result**: Implementation review complete. No open Critical items.
