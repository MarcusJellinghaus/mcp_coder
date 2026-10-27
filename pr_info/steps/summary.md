# Summary — #1331: Move shared approval pilot helpers into `tests/icoder/_app_pilot_approval_helpers.py`

Part of epic #353. Follow-up of #1323 (merged). Pure move. Process: `docs/processes-prompts/refactoring-guide.md`.

## Problem
`tests/icoder/test_app_pilot.py` (510 lines) ends with six approval helpers (lines 444–510). None of its own tests use them. The two approval test files import them from the base test file:

| Symbol | Kind | Def-time dependency |
|---|---|---|
| `_APPROVAL_TOOL` | constant | — |
| `_approval_event` | function | default arg `tool_name=_APPROVAL_TOOL` |
| `_RecordingEngine(ApprovalEngine)` | class | — |
| `_isolate_user_layer` | function | — |
| `_author_project_ask` | function | — (reads `_APPROVAL_TOOL` in body) |
| `_open_modal_and_press` | async function | default arg `tool_name=_APPROVAL_TOOL` |

## Architectural / design change
- **New shared test-helper module** `tests/icoder/_app_pilot_approval_helpers.py`. It is not a test module: the leading `_` and no `test_` prefix keep pytest from collecting it. Precedent: `tests/_import_walker.py`, `tests/llm/providers/claude/_mcp_stub_server.py`.
- **Dependency direction after the change:**
  - `test_app_pilot_approval.py` → `_app_pilot_approval_helpers.py`
  - `test_app_pilot_approval_persist.py` → `_app_pilot_approval_helpers.py`
  - Neither approval file imports from `test_app_pilot.py` any more.
  - `test_app_pilot.py` imports nothing from the new module, so no import cycle is possible.
- **Unchanged:** `_submit_and_wait` stays in `test_app_pilot.py`. The streaming, cancel, content-units and shutdown siblings keep importing it from there.
- **Not in the new module:** no `pytestmark` (it has no tests) and no module docstring (`D` is ignored for `tests/**`). It is not a `conftest.py`, because these are plain helpers, not fixtures.
- **Def-time safety:** `_APPROVAL_TOOL` must sit above `_approval_event` and `_open_modal_and_press` in the new module, or the import raises `NameError`. `move_symbol` decides placement. Symbols are never reordered by hand.
- No production code (`src/`), import-linter contract, `tach.toml` or `.large-files-allowlist` change.

## Files

| Path | Action |
|---|---|
| `tests/icoder/_app_pilot_approval_helpers.py` | **create** (six moved symbols plus the imports `move_symbol` writes) |
| `tests/icoder/test_app_pilot.py` | modify: the six symbols leave; unused imports are removed (`ApprovalDecision`, `ApprovalEngine`, `ApprovalModal`, `StreamEvent`) |
| `tests/icoder/test_app_pilot_approval.py` | modify: import only, now from `tests.icoder._app_pilot_approval_helpers` |
| `tests/icoder/test_app_pilot_approval_persist.py` | modify: import only, now from `tests.icoder._app_pilot_approval_helpers` |

No folders are created; `tests/icoder/` is already a package.

## TDD note
This is a pure move. No new tests are written. The existing 33 tests in the two approval files (22 + 11) and the 19 in `test_app_pilot.py` are the safety net. The step records collect counts before the move and checks they match after it.

## Steps
- **Step 1**: the whole move, in one commit (`step_1.md`).

## Rules (from #1323 / #1331)
- Pure move: no body, decorator, default-argument or docstring changes.
- Refactoring tools only (`move_symbol`; `run_ruff_fix` for imports). MCP tools only.
- Any precondition or acceptance check that fails → write one line to `pr_info/.blocked.txt` and stop.
