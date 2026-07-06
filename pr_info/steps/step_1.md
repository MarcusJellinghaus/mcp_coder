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
- Remove imports left unused in `prompt_manager.py` after the parsing helpers leave —
  namely `re` and `Union` (both move to `prompt_parsing.py`). Use
  `mcp__mcp-tools-py__run_ruff_fix` selecting **F401** (unused-import), or explicitly
  delete those two named imports. Do **not** rely on `run_format_code` for this — it
  runs black + isort only, neither of which removes unused imports. `Dict`/`Any`/`List`
  remain in use by the public functions; leave them.

## ALGORITHM — move procedure (no new logic)
```
for each of the 3 parsing functions:  move_symbol(prompt_manager.py -> prompt_parsing.py, dry_run) ; review ; execute
for each of the 3 parsing test classes: move_symbol(test_prompt_manager.py -> test_prompt_parsing.py, dry_run) ; review ; execute
run_ruff_fix (F401)                   # remove now-unused imports (`re`, `Union`) — NOT run_format_code
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

## Import-linter note (deferred to Step 2)
`prompt_manager` is a named layer in `.importlinter`
(`mcp_coder.llm | mcp_coder.prompt_manager`). Do **not** edit `.importlinter` in this
step: the planned sub-layer names BOTH new modules
(`mcp_coder.prompt_sources | mcp_coder.prompt_parsing`), and `prompt_sources.py` does not
exist yet. After Step 1, `prompt_parsing.py` exists but stays unlisted/floating — that is
expected and does not fail `run_lint_imports_check`. The `.importlinter` edit lands in
Step 2, once both modules exist.

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
> remove the `src/mcp_coder/prompt_manager.py` line from `.large-files-allowlist`. Do NOT
> edit `.importlinter` in this step (deferred to Step 2). Use MCP tools exclusively.
> Remove the now-unused `re` and `Union` imports from `prompt_manager.py` with
> `run_ruff_fix` (F401) — not `run_format_code`, which does not remove unused imports.
> Then confirm `compact-diff` shows only import/
> file-header changes, and that `check_file_size`, `run_lint_imports_check`,
> `run_pytest_check` (`-n auto` with the unit-exclusion markers), `run_pylint_check`, and
> `run_mypy_check` all pass. Produce exactly one commit.
