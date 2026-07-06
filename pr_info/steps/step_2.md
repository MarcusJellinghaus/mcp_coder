# Step 2 — Extract `prompt_sources.py` + mirror tests

**Read `pr_info/steps/summary.md` first.** This is the sources half of the pure
"Move, Don't Change" split of `prompt_manager.py` (Issue #1031), completing the split.
Whole functions relocate; **only imports change**. One commit. Do Step 1 first.

## Goal
Move the four path-resolution / content-loading helpers out of `prompt_manager.py` into
a new `prompt_sources.py`, and move their four mirror test classes into a new
`test_prompt_sources.py`. `prompt_manager.py` finishes at ~450 lines.

## WHERE
- **New:** `src/mcp_coder/prompt_sources.py`
- **New:** `tests/test_prompt_sources.py`
- **Modified:** `src/mcp_coder/prompt_manager.py` (helpers removed, import added)
- **Modified:** `tests/test_prompt_manager.py` (4 classes removed — leaves the 4 public-API classes)
- **Modified:** `.importlinter` (add sub-layer beneath `prompt_manager` — both new modules now exist)

## WHAT — symbols to move (signatures unchanged, do not edit bodies)
Source helpers → `prompt_sources.py` (move all four together so their internal calls
stay intra-module):
- `_is_package_relative_path(source: str) -> bool`
- `_resolve_package_path(source: str) -> Optional[Path]`
- `_load_content(source: str) -> str`
- `_is_file_path(source: str) -> bool`

Test classes → `tests/test_prompt_sources.py`:
- `TestGetPromptFromFile`
- `TestGetPromptWildcard`
- `TestInputAutoDetection`
- `TestPackageIntegration`

## HOW — integration points
- Use `mcp__mcp-tools-py__move_symbol` for all moves; `dry_run=True` first, then execute.
  Pass the four helpers in a single call (`symbol_names=[...]`) so `_load_content`'s calls
  to `_is_file_path`, `_is_package_relative_path`, `_resolve_package_path` remain internal
  to `prompt_sources.py` rather than becoming cross-module imports.
- `prompt_sources.py` must end up with module-level imports: `import glob`, `import os`,
  `from pathlib import Path`, `from typing import Optional`, and
  `from .utils.data_files import find_data_file`. Verify after the move; add any the tool
  did not carry.
- After the source move, `prompt_manager.py` must contain
  `from .prompt_sources import _is_file_path, _load_content` (only these **2** are called
  by the public functions; `_is_package_relative_path` and `_resolve_package_path` stay
  fully encapsulated in `prompt_sources`).
- The 4 test classes import the **public API**, not `prompt_sources`. Verify the API
  import plus `os`/`tempfile`/`Path`/`patch`/`pytest` landed in `test_prompt_sources.py`.
- Remove imports left unused in `prompt_manager.py` after these helpers leave — namely
  `Optional`, `Path`, and `find_data_file`. Use `mcp__mcp-tools-py__run_ruff_fix`
  selecting **F401** (unused-import), or explicitly delete those three named imports. Do
  **not** rely on `run_format_code` — it runs black + isort only, neither of which
  removes unused imports. Note: `glob` and `os` **remain in use** by the public
  `validate_prompt_directory` (`glob.glob`, `os.path.*`) — do **not** delete them.
- **Edit `.importlinter`** (now that both new modules exist): insert a new sub-layer line
  **directly beneath** `mcp_coder.llm | mcp_coder.prompt_manager` in the
  `layered_architecture` contract, so the block reads:
  ```
  mcp_coder.llm | mcp_coder.prompt_manager
  mcp_coder.prompt_sources | mcp_coder.prompt_parsing
  mcp_coder.prompts
  ```
  This constrains both new modules beneath `prompt_manager` (which imports them). Do
  **not** append them to the `prompt_manager` line with `|`: same-line siblings may not
  import each other, and `prompt_manager` imports both — that would break the contract.
  The `|` between the two new modules is correct: they are independent siblings (no
  cross-calls). `run_lint_imports_check` must PASS after this edit.

## ALGORITHM — move procedure (no new logic)
```
move_symbol(prompt_manager.py -> prompt_sources.py, [4 helpers], dry_run) ; review ; execute
for each of the 4 source test classes: move_symbol(test_prompt_manager.py -> test_prompt_sources.py, dry_run) ; review ; execute
run_ruff_fix (F401)                   # remove now-unused imports (`Optional`, `Path`, `find_data_file`) — NOT run_format_code
edit .importlinter                    # add sub-layer: prompt_sources | prompt_parsing beneath prompt_manager
compact-diff                          # assert ONLY imports + file headers changed (+ .importlinter sub-layer line)
run full check suite                  # regression gate — existing tests must pass
```

## DATA — no data structures change
Return types and shapes are identical to today; this step relocates code only. The
existing test suite is the acceptance gate proving behavior is unchanged.

## Acceptance checks (all must pass — MCP tools)
- `compact-diff` shows only import changes + new/deleted file headers.
- `tests/test_prompt_manager.py` now contains exactly the 4 public-API classes
  (`TestGetPromptFromString`, `TestValidatePromptMarkdown`, `TestValidatePromptDirectory`,
  `TestGetPromptWithSubstitutions`).
- `mcp__mcp-workspace__check_file_size` — all touched files under 750 (stays off the
  allowlist from Step 1).
- `.importlinter` contains the new sub-layer
  `mcp_coder.prompt_sources | mcp_coder.prompt_parsing` directly beneath the
  `mcp_coder.llm | mcp_coder.prompt_manager` line.
- `run_lint_imports_check` — must PASS with the new sub-layer present (both new modules
  constrained beneath `prompt_manager`); `run_pytest_check` (`-n auto`, unit-exclusion
  markers), `run_pylint_check`, `run_mypy_check` pass; `tach check` (Bash) passes.

## LLM prompt for this step
> Implement **Step 2** of `pr_info/steps/summary.md` (Issue #1031), following
> `pr_info/steps/step_2.md` exactly. Do Step 1 first. This is a pure "Move, Don't Change"
> refactor — use `mcp__mcp-tools-py__move_symbol` (dry-run first) to move the four helpers
> `_is_package_relative_path`, `_resolve_package_path`, `_load_content`, `_is_file_path`
> (in one call) from `src/mcp_coder/prompt_manager.py` into a new
> `src/mcp_coder/prompt_sources.py`, and the four test classes `TestGetPromptFromFile`,
> `TestGetPromptWildcard`, `TestInputAutoDetection`, `TestPackageIntegration` from
> `tests/test_prompt_manager.py` into a new `tests/test_prompt_sources.py`. Do not edit any
> function/class body. Verify `prompt_sources.py` carries `import glob`, `import os`,
> `from pathlib import Path`, `from typing import Optional`, and
> `from .utils.data_files import find_data_file`; that `prompt_manager.py` now imports only
> `_is_file_path, _load_content` from `.prompt_sources`; and that `test_prompt_manager.py`
> is left with exactly the four public-API test classes. Then edit `.importlinter`: add
> the sub-layer `mcp_coder.prompt_sources | mcp_coder.prompt_parsing` directly beneath the
> `mcp_coder.llm | mcp_coder.prompt_manager` line (do NOT append the new modules to that
> line with `|`). Use MCP tools exclusively. Remove the now-unused `Optional`, `Path`, and
> `find_data_file` imports from `prompt_manager.py` with `run_ruff_fix` (F401) — not
> `run_format_code`, which does not remove unused imports; keep `glob` and `os` (still used
> by `validate_prompt_directory`). Then confirm `compact-diff` shows only import/file-header
> changes plus the `.importlinter` sub-layer line, and
> that `check_file_size`, `run_lint_imports_check` (PASS with the new sub-layer),
> `run_pytest_check` (`-n auto` with the
> unit-exclusion markers), `run_pylint_check`, and `run_mypy_check` all pass. Produce
> exactly one commit.
