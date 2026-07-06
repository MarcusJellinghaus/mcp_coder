# Step 1 — Extract `prompt_parsing.py` + mirror tests + remove allowlist entry

**Read `pr_info/steps/summary.md` first.** This is the parsing half of a pure
"Move, Don't Change" split of `prompt_manager.py` (Issue #1031). Whole functions
relocate; **only imports change**. One commit.

## Goal
Move the three markdown-parsing helpers out of `prompt_manager.py` into a new
`prompt_parsing.py`, move their three mirror test classes into a new
`test_prompt_parsing.py`, and remove the now-stale `.large-files-allowlist` entry
(this move drops `prompt_manager.py` from 772 to ~668 lines — under the 750 limit).

## WHERE
- **New:** `src/mcp_coder/prompt_parsing.py`
- **New:** `tests/test_prompt_parsing.py`
- **Modified:** `src/mcp_coder/prompt_manager.py` (helpers removed, import added)
- **Modified:** `tests/test_prompt_manager.py` (3 classes removed)
- **Modified:** `.large-files-allowlist` (remove `src/mcp_coder/prompt_manager.py`)

## WHAT — symbols to move (signatures unchanged, do not edit bodies)
Source helpers → `prompt_parsing.py`:
- `_extract_headers(content: str) -> List[Dict[str, Any]]`
- `_extract_code_block_after_header(content: str, header: Dict[str, Any]) -> Union[str, None]`
- `_find_duplicates(items: List[str]) -> List[str]`

Test classes → `tests/test_prompt_parsing.py`:
- `TestGetPromptMissingHeader`
- `TestGetPromptDuplicateHeaders`
- `TestHeaderLevelMatching`

## HOW — integration points
- Use `mcp__mcp-tools-py__move_symbol` for **all four moves** (it relocates whole
  symbols, auto-creates destination files, and rewrites imports project-wide). Run each
  with `dry_run=True` first, inspect, then execute.
- `prompt_parsing.py` must end up with module-level imports: `import re` and
  `from typing import Any, Dict, List, Union`. Verify after the move; add any the tool
  did not carry.
- After the source move, `prompt_manager.py` must contain
  `from .prompt_parsing import _extract_headers, _extract_code_block_after_header, _find_duplicates`
  (move_symbol inserts this automatically because the public functions call them).
- The 3 test classes import the **public API** (`from mcp_coder.prompt_manager import ...`)
  plus `os`, `tempfile`, `Path`, `patch`, `pytest` as used — **not** the new module.
  Verify these landed in `test_prompt_parsing.py`.
- Run `mcp__mcp-tools-py__run_format_code` to remove any import left unused in
  `prompt_manager.py` after the parsing helpers leave (e.g. `re`). `Dict`/`Any`/`List`/
  `Union` may still be used by the public functions — let the formatter decide; do not
  hand-prune.

## ALGORITHM — move procedure (no new logic)
```
for each of the 3 parsing functions:  move_symbol(prompt_manager.py -> prompt_parsing.py, dry_run) ; review ; execute
for each of the 3 parsing test classes: move_symbol(test_prompt_manager.py -> test_prompt_parsing.py, dry_run) ; review ; execute
run_format_code                       # sweep now-unused imports
edit .large-files-allowlist           # delete the src/mcp_coder/prompt_manager.py line
compact-diff                          # assert ONLY imports + file headers changed
run full check suite                  # regression gate — existing tests must pass
```
(Multiple symbols may be passed in one `move_symbol` call via `symbol_names`.)

## DATA — no data structures change
Return types and shapes are identical to today; this step relocates code only. The
existing test suite is the acceptance gate proving behavior is unchanged.

## Acceptance checks (all must pass — MCP tools)
- `compact-diff` shows only import changes + new/deleted file headers.
- `mcp__mcp-workspace__check_file_size` — `prompt_manager.py` under 750 **and** no longer
  in `.large-files-allowlist` (no stale-entry report).
- `run_lint_imports_check`, `run_pytest_check` (`-n auto`, unit-exclusion markers),
  `run_pylint_check`, `run_mypy_check` pass; `tach check` (Bash) passes.

## LLM prompt for this step
> Implement **Step 1** of `pr_info/steps/summary.md` (Issue #1031), following
> `pr_info/steps/step_1.md` exactly. This is a pure "Move, Don't Change" refactor —
> use `mcp__mcp-tools-py__move_symbol` (dry-run first) to move the three parsing helpers
> `_extract_headers`, `_extract_code_block_after_header`, `_find_duplicates` from
> `src/mcp_coder/prompt_manager.py` into a new `src/mcp_coder/prompt_parsing.py`, and the
> three test classes `TestGetPromptMissingHeader`, `TestGetPromptDuplicateHeaders`,
> `TestHeaderLevelMatching` from `tests/test_prompt_manager.py` into a new
> `tests/test_prompt_parsing.py`. Do not edit any function/class body. Verify
> `prompt_parsing.py` carries `import re` and `from typing import Any, Dict, List, Union`,
> and that `prompt_manager.py` now imports the three helpers from `.prompt_parsing`. Then
> remove the `src/mcp_coder/prompt_manager.py` line from `.large-files-allowlist`. Use MCP
> tools exclusively. Run `run_format_code`, then confirm `compact-diff` shows only import/
> file-header changes, and that `check_file_size`, `run_lint_imports_check`,
> `run_pytest_check` (`-n auto` with the unit-exclusion markers), `run_pylint_check`, and
> `run_mypy_check` all pass. Produce exactly one commit.
