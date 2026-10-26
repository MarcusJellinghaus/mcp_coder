# Summary — Split `tests/workflows/vscodeclaude/test_session_restart.py` (#1324)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal
`test_session_restart.py` is one class (`TestSessionRestart`, 16 tests, 924 lines) and is listed in `.large-files-allowlist`.
Split it into four classes, move each class to its own file, move the shared helper `_make_assessment` to `conftest.py`, and delete the emptied original. Then remove its allowlist entry.

## Hard rules (apply to every step)
- **This is a pure refactoring. Move code; don't change it.** No logic edits, renames, test deletions or merges, and no reformatting beyond what `run_format_code` does.
- **Only allowed edits:**
  - import lines;
  - the four 2-line class headers in step 1;
  - deleting the drained file;
  - the one `.large-files-allowlist` line.
- **Move code only with `mcp__mcp-tools-py__move_symbol`.** Always do a dry run first. Never move code by hand.
- **Use MCP tools only, no Bash** (commits use the approved git commands).
- **Locate code by symbol name or `def` name, never by line number.**
- **Failure action:** if a precondition or gate fails, undo the step's moves with `move_symbol` (move the symbol back), write one line to `pr_info/.blocked.txt` and stop.
- **Call sites stay bare.** Any `conftest._make_assessment(` or `test_session_restart._make_assessment(` in a method body means rope rewrote a call site. That counts as a failed gate.

## Architectural / design changes
- **Production code:** none. `src/mcp_coder/workflows/vscodeclaude/session_restart.py` and `session_launch.py` stay as they are.
- **Test layout:** tests now follow the "one source module → prefixed sibling test files" convention.
  - `session_restart.py` tests: `test_session_restart_{lifecycle,issue_status,cache,closed_sessions,prepare_branch,branch_integration}.py`.
  - There is no base `test_session_restart.py` any more, which removes the catch-all class.
  - `session_launch.py` tests: `test_session_launch*.py`. The 4 `session_launch` tests that were misplaced in the restart file move there.
- **Shared helper:** `_make_assessment` moves verbatim to `tests/workflows/vscodeclaude/conftest.py`. The two `restart_closed_sessions` test files import it explicitly with `from tests.workflows.vscodeclaude.conftest import _make_assessment`, the style the directory already uses for `_build_assessment`. The seven other local `_make_assessment` copies are not touched; consolidating them is #1333.
- **Four new class names,** each naming the function under test plus the concern:
  - `TestPrepareAndLaunchSession`
  - `TestProcessEligibleIssuesMaxSessions`
  - `TestRestartClosedSessionsLifecycle`
  - `TestRestartClosedSessionsIssueStatus`
- **Fixture scope:** unchanged. All files stay in `tests/workflows/vscodeclaude/`, and `conftest.py` has no autouse fixtures.

## Test groups (source order inside `TestSessionRestart`)
| Group | First `def` of group | Tests | New class | Destination |
|---|---|---:|---|---|
| A | `test_prepare_and_launch_session_success` | 3 | `TestPrepareAndLaunchSession` | `test_session_launch_prepare.py` (new) |
| B | `test_process_eligible_issues_respects_max_sessions` | 1 | `TestProcessEligibleIssuesMaxSessions` | `test_session_launch_process_issues.py` (existing) |
| C | `test_restart_closed_sessions_removes_orphans` | 5 | `TestRestartClosedSessionsLifecycle` | `test_session_restart_lifecycle.py` (new) |
| D | `test_restart_closed_sessions_skips_blocked_issues` | 7 | `TestRestartClosedSessionsIssueStatus` | `test_session_restart_issue_status.py` (new) |

## Files created / modified / deleted
All test files are in `tests/workflows/vscodeclaude/`.

| File | Change |
|---|---|
| `test_session_restart.py` | Step 1: 4 class headers inserted. Steps 2–5: drained. Step 5: **deleted** |
| `test_session_launch_prepare.py` | **Created** (step 2): group A, ~215 lines |
| `test_session_launch_process_issues.py` | **Modified** (step 3): group B class appended; import block unchanged; 6 → 7 tests, ~480 lines |
| `test_session_restart_lifecycle.py` | **Created** (step 4): group C, ~250 lines |
| `test_session_restart_issue_status.py` | **Created** (step 5): group D, ~425 lines |
| `conftest.py` | **Modified** (step 5): `_make_assessment` added verbatim; `Decision` and `SessionAction` added to the existing `types` import block |
| `.large-files-allowlist` (repo root) | **Modified** (step 5): the line `tests/workflows/vscodeclaude/test_session_restart.py` removed (matched by text) |

No new folders or `__init__.py` files, and no changes to `.importlinter`, `tach.toml` or `vulture_whitelist.py`.

## Baseline (measured 2026-10-26)
- `tests/workflows/vscodeclaude/` collect-only: **688** tests. This must stay 688 after every step.
- `test_session_restart.py` collects **16**, `test_session_launch_process_issues.py` collects **6**, and both together give **22 passed**.

## Steps (one commit each)
1. Insert four class headers in `test_session_restart.py`.
2. Move group A → `test_session_launch_prepare.py`.
3. Move group B → `test_session_launch_process_issues.py`.
4. Move group C → `test_session_restart_lifecycle.py`. This adds a temporary import of `_make_assessment` from `test_session_restart`.
5. Move group D → `test_session_restart_issue_status.py`, then move `_make_assessment` → `conftest.py`, delete the drained original, and update the allowlist.

## Standard checks (end of every step)
1. `mcp__mcp-tools-py__run_format_code`
2. `mcp__mcp-tools-py__run_ruff_check`. Must be clean. If it reports `F401` only in files this step touched, run `mcp__mcp-tools-py__run_ruff_fix(select=["F401"], target_directories=["tests/workflows/vscodeclaude"])`, then run `run_ruff_check` again.
3. `mcp__mcp-tools-py__run_pylint_check`
4. `mcp__mcp-tools-py__run_mypy_check`
5. `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "<fast-unit marker exclusion from CLAUDE.md>"]`
6. `mcp__mcp-tools-py__run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/"])` → **688**
7. `mcp__mcp-workspace__git` diff with `compact=true` → only moved blocks (suppressed), import changes, and the allowed edits for that step.

## Testing approach (TDD note)
This is a pure move, so no new tests are written. The existing 16 tests are the safety net. Every step checks per-class collect counts and pass results before and after its move.
