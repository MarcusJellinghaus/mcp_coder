# Summary — Split `tests/icoder/test_app_pilot.py` (#1323)

Part of epic #353. Process: `docs/processes-prompts/refactoring-guide.md`. Follow-up: #1331.

## Goal

`tests/icoder/test_app_pilot.py` (2442 lines, 96 collected tests, allowlisted) becomes a base file plus six
prefixed sibling files, one per app concern, all under 750 lines. Its entry in `.large-files-allowlist` is removed.
This is a **pure refactoring of tests only**. `src/` is not changed.

## Architectural / design changes

There are no production changes. The test layout changes as follows:

| Before | After |
|---|---|
| One 2442-line pilot file that holds fixtures, helpers and every concern | The base file (app shell plus shared helpers) and six concern files |
| Fixtures `icoder_app`, `make_icoder_app` are module-local | Both move to `tests/icoder/conftest.py` and are shared with the siblings |
| — | The siblings import only underscore-prefixed shared helpers from `tests.icoder.test_app_pilot` |

Design decisions (fixed by the issue, not up for re-discussion):
- **Prefixed siblings in `tests/icoder/`**, not `tests/icoder/ui/`. `ui/conftest.py` has a different
  `make_icoder_app` that would shadow the moved one.
- **Shared helpers stay in the base file**: `_submit_and_wait`, `_APPROVAL_TOOL`, `_approval_event`, `_RecordingEngine`,
  `_isolate_user_layer`, `_author_project_ask`, `_open_modal_and_press`. The default `tool_name=_APPROVAL_TOOL` is
  evaluated at def time, so these keep their current order. They never move. Moving them out is #1331.
- **Single-destination helpers move with their tests**, always *after* their last caller and in their own call.
- **Each new file gets a verbatim copy of `pytestmark = pytest.mark.textual_integration`**, so no test loses its
  marker. CI's unit-test job excludes `textual_integration`.
- **Eleven section-banner comments are deleted** from the base file: eight left with no code under them, and three whose wording goes stale.

## Files

| Path | Action | Final tests (collected) |
|---|---|---:|
| `tests/icoder/conftest.py` | modified: + fixtures `icoder_app`, `make_icoder_app`, + 4 imports | — |
| `tests/icoder/test_app_pilot.py` | modified: drained to the app shell + shared helpers | 19 |
| `tests/icoder/test_app_pilot_streaming.py` | created | 20 |
| `tests/icoder/test_app_pilot_cancel.py` | created | 5 |
| `tests/icoder/test_app_pilot_content_units.py` | created | 16 |
| `tests/icoder/test_app_pilot_approval.py` | created | 22 |
| `tests/icoder/test_app_pilot_approval_persist.py` | created | 11 |
| `tests/icoder/test_app_pilot_shutdown.py` | created | 3 |
| `.large-files-allowlist` | modified: remove the `tests/icoder/test_app_pilot.py` line | — |

Invariants: the 7 files hold **96** tests in total, `tests/icoder/` collects **1062** and the whole suite **6463**. If the
baseline in step 1 differs, use the recorded baseline numbers instead.

## TDD in a pure refactoring

There is no new behaviour, so no new tests are written. The moved tests *are* the tests. Each step proves itself by:
1. **Collect counts** (`--collect-only -q`, no marker filter) matching the expected numbers before and after.
2. **Running** the destination file and the base file. Every test that passed before passes now.
3. **The marker check**: `-m "not textual_integration"` on the new file finds "No Tests Found".

## Common rules (apply to every step)

**Allowed edits only.** These are allowed: import statements; one verbatim `pytestmark = pytest.mark.textual_integration`
line per new file; `import pytest` in a new file that has none; deleting the eleven banners listed in step 8; the
`.large-files-allowlist` line. Nothing else is hand-edited: no body, decorator, docstring or comment changes, no renames, no reordering.

**Tools only.** Use MCP tools only, no Bash. Moves go through `mcp__mcp-tools-py__move_symbol`: dry run first, then the real call, in exactly
the listed order. Each list is in source order and has 6 or fewer symbols.

**Dry-run gate (every call).** The preview may change only `tests/icoder/test_app_pilot.py` and that step's
destination. It must contain no body reference qualified as `test_app_pilot.` / `conftest.`. A helper call rewritten to
`module.helper(...)` counts as a failure.

**Import fix after each step's moves** (import-only edits):
- Delete any `from tests.icoder.test_app_pilot import X` where `X` is now defined in the same file (expected
  for the constant moved last).
- Remove whatever ruff `F401` reports, in the destination **and** in `test_app_pilot.py`.
- `mcp_coder` names must import from the same module as in the original file (lines 21–45).
- Imports from the base file name only underscore-prefixed helpers. Never import `test_*`, a fixture or `pytestmark`.
- A function-local or method-local import stays where it is.

**Checks closing every step** (all must pass before the commit):
- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_ruff_check`, `run_pylint_check`, `run_mypy_check`
- `run_pytest_check(extra_args=["--collect-only", "-q", "tests/icoder/"])` gives 1062
- `run_pytest_check(extra_args=["-q", "-n", "auto", <base file>, <files created so far>], timeout_seconds=600)`: all pass
- For each new file: `run_pytest_check(extra_args=["-q", "-m", "not textual_integration", <new file>])` gives "No Tests Found"

**Blocked handling.** If any of these happens, write one line to `pr_info/.blocked.txt` and stop:
- a precondition fails
- a dry-run gate fails
- a real `move_symbol` call times out or reports `Token … cannot be matched`
- a count differs
- a shared helper leaves the base file
- a test that passed before fails
- an edit outside the allowed list would be needed

Never revert or reorder by hand.

## Steps

1. Baseline + fixtures → `conftest.py`
2. Streaming → `test_app_pilot_streaming.py`
3. Cancel → `test_app_pilot_cancel.py`
4. Content units → `test_app_pilot_content_units.py`
5. Approval → `test_app_pilot_approval.py`
6. Approval persist → `test_app_pilot_approval_persist.py`
7. Shutdown → `test_app_pilot_shutdown.py`
8. Banner cleanup, allowlist removal, final verification
