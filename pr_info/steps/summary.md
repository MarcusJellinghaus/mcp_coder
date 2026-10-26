# Summary — Split `cli/parsers.py` + `tests/cli/test_main.py` (#1315)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal
Get `src/mcp_coder/cli/parsers.py` (753 lines) and `tests/cli/test_main.py` (870 lines)
under 750 lines and off `.large-files-allowlist`. Use a **pure move**: no logic edits,
no renames, no test deletions or merges.

## Architectural / design changes
- **One parser module per help category** (`command_catalog.COMMAND_CATEGORIES`):
  - `cli/parsers.py`: base classes (`HelpHintArgumentParser`, `WideHelpFormatter`) +
    TOOLS (`prompt`, `commit`, `check`) + SETUP (`verify`, `init`, `install`).
  - `cli/workflow_parsers.py` (new): BACKGROUND DEVELOPMENT (`implement`, `review-plan`,
    `review-implementation`, `create-plan`, `rebase`, `create-pr`, `fix-conflict`,
    `fix-ci`, `coordinator`). New workflow commands land here from now on.
  - `cli/interactive_parsers.py` (new): INTERACTIVE DEVELOPMENT (`vscodeclaude`, `icoder`).
  - `cli/gh_parsers.py`: unchanged (rest of TOOLS).
- **Dependency direction:** `workflow_parsers` / `interactive_parsers` → `.parsers`
  (`WideHelpFormatter`), `.command_catalog`, `.shared_args`, the same way `gh_parsers.py`
  does it. `parsers.py` imports neither new module, so there is no cycle.
  `main.create_parser` stays the only src consumer. Its body (and so subparser
  registration order and `--help` output) is unchanged; only its import block changes.
- **Flat sibling modules**, no `cli/parsers/` package. This matches `gh_parsers.py`,
  `shared_args.py` and `command_catalog.py`.
- **Tests mirror the parser modules:** `test_parsers.py`, `test_workflow_parsers.py`,
  `test_interactive_parsers.py`, `test_gh_parsers.py`. The `main()`-driven coordinator
  tests go to the prefixed sibling `test_main_coordinator.py`.
- No `.importlinter` / `tach.toml` change: there is no contract inside `mcp_coder.cli`.

## Ground rules (apply to every step)
- Move code only with `mcp__mcp-tools-py__move_symbol`, dry run first. Never move code by
  hand and never reorder symbols by hand.
- Only allowed edits: import lines; the one-line module docstring +
  `from __future__ import annotations` on each new **src** module; the
  `command_catalog.py` docstring file-name list; `.large-files-allowlist`.
- No stubs, no re-exports.
- MCP tools only, no Bash.
- This is a pure refactoring, so there are no new tests. The existing suite plus
  `--collect-only` counts are the safety net: each step records the counts first and
  compares them afterwards.
- Run pytest with `-n auto` and the fast-unit marker exclusion from `CLAUDE.md`.

## Files created / modified
| Path | Change | Step |
|---|---|---|
| `src/mcp_coder/cli/workflow_parsers.py` | **new** (9 `add_*` functions) | 1 |
| `src/mcp_coder/cli/interactive_parsers.py` | **new** (2 `add_*` functions) | 1 |
| `src/mcp_coder/cli/parsers.py` | modified (11 functions removed) | 1 |
| `src/mcp_coder/cli/main.py` | modified (import block only) | 1 |
| `src/mcp_coder/cli/command_catalog.py` | modified (docstring lines 5–7) | 1 |
| `.large-files-allowlist` | remove `src/mcp_coder/cli/parsers.py` | 1 |
| `tests/cli/test_workflow_parsers.py` | **new** | 2 |
| `tests/cli/test_interactive_parsers.py` | **new** | 2 |
| `tests/cli/test_gh_parsers.py` | **new** | 2 |
| `tests/cli/test_parsers.py` | modified (5 classes out in step 2; 1 function + 1 class in, step 3) | 2, 3 |
| `tests/cli/test_main_coordinator.py` | **new** | 3 |
| `tests/cli/test_main.py` | modified (4 symbols removed) | 3 |
| `.large-files-allowlist` | remove `tests/cli/test_main.py` | 3 |

## Steps
1. `step_1.md`: split the src `parsers.py` into three modules.
2. `step_2.md`: split `test_parsers.py` to mirror the new parser modules.
3. `step_3.md`: split `test_main.py` (coordinator tests → `test_main_coordinator.py`;
   parser tests → `test_parsers.py`).

## Expected test counts (`--collect-only -q`, no marker filter)
| File | Before | After step 2 | After step 3 |
|---|---:|---:|---:|
| `test_main.py` | 71 | 71 | 39 |
| `test_main_coordinator.py` | — | — | 10 |
| `test_parsers.py` | 34 | 12 | 32 |
| `test_workflow_parsers.py` | — | 10 | 10 |
| `test_interactive_parsers.py` | — | 7 | 7 |
| `test_gh_parsers.py` | — | 7 | 7 |
| `tests/cli/` | baseline | baseline | baseline |
