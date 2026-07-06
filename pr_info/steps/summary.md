## Summary — Split `prompt_manager.py` + `test_prompt_manager.py` (Issue #1031)

Part of the oversized-file cleanup (umbrella #353). `src/mcp_coder/prompt_manager.py`
is **772 lines** — over the **750** hard limit enforced in CI
(`check file-size --max-lines 750`) and currently grandfathered in
`.large-files-allowlist`. This is a **pure "Move, Don't Change" refactor**: whole
private helper functions relocate into two new sibling modules; **only imports
change**. The test file is split thematically to mirror the new source layout.

**Definition of done:** `prompt_manager.py` is under 750 lines **and** removed from
`.large-files-allowlist`, with the public API and all behavior unchanged.

### Architectural / design changes

The design change is a **cohesion split**, not a behavior or API change:

- `prompt_manager.py` becomes a thin **public-API + orchestration** module. Its four
  public functions (`get_prompt`, `get_prompt_with_substitutions`,
  `validate_prompt_markdown`, `validate_prompt_directory`) stay put, so **all external
  import paths are unchanged** — no consumer is affected.
- Two cohesive groups of private helpers move into siblings **in the same layer**:
  - `prompt_sources.py` — path resolution + content loading (filesystem / package I/O).
  - `prompt_parsing.py` — pure markdown-string parsing (no I/O).
- The two helper groups are **independent siblings** (verified in code: no cross-calls
  between them). Both are consumed only by `prompt_manager.py`. Because they sit in the
  **same architecture layer**, **no import-linter sub-layer is needed** and
  `prompt_manager` is not named in any import-linter contract.
- After the move, `prompt_manager.py` imports **2** names from `prompt_sources`
  (`_load_content`, `_is_file_path`) and **3** from `prompt_parsing`
  (`_extract_headers`, `_extract_code_block_after_header`, `_find_duplicates`).
  `_is_package_relative_path` and `_resolve_package_path` stay **fully encapsulated**
  inside `prompt_sources` (the manager never calls them directly).
- **Tests** split into three files mirroring the three source modules. Every test class
  exercises the **public API** — there are no direct private-helper tests — so all three
  test files import from `mcp_coder.prompt_manager`, **not** from the new modules. The
  split is thematic (which module's behavior is under test), a structural mirror only;
  the test file is already under 750, so this is not a CI requirement.

### Target module layout (verified against code)

| File | Holds | ~lines |
|---|---|---|
| `src/mcp_coder/prompt_manager.py` *(keep)* | `get_prompt`, `get_prompt_with_substitutions`, `validate_prompt_markdown`, `validate_prompt_directory` | ~450 |
| `src/mcp_coder/prompt_sources.py` *(new)* | `_is_package_relative_path`, `_resolve_package_path`, `_load_content`, `_is_file_path` | ~220 |
| `src/mcp_coder/prompt_parsing.py` *(new)* | `_extract_headers`, `_extract_code_block_after_header`, `_find_duplicates` | ~110 |

Test class distribution (fixed by the issue — 4 / 4 / 3):

| File | Classes |
|---|---|
| `tests/test_prompt_manager.py` *(keep)* | `TestGetPromptFromString`, `TestValidatePromptMarkdown`, `TestValidatePromptDirectory`, `TestGetPromptWithSubstitutions` |
| `tests/test_prompt_sources.py` *(new)* | `TestGetPromptFromFile`, `TestGetPromptWildcard`, `TestInputAutoDetection`, `TestPackageIntegration` |
| `tests/test_prompt_parsing.py` *(new)* | `TestGetPromptMissingHeader`, `TestGetPromptDuplicateHeaders`, `TestHeaderLevelMatching` |

### Folders / modules / files created or modified

**Created**
- `src/mcp_coder/prompt_parsing.py` — parsing helpers (Step 1)
- `tests/test_prompt_parsing.py` — parsing test classes (Step 1)
- `src/mcp_coder/prompt_sources.py` — source/loading helpers (Step 2)
- `tests/test_prompt_sources.py` — source test classes (Step 2)
- `pr_info/steps/summary.md`, `step_1.md`, `step_2.md` — these planning docs

**Modified**
- `src/mcp_coder/prompt_manager.py` — helpers removed; imports added; unused imports swept
- `tests/test_prompt_manager.py` — drained test classes removed
- `.large-files-allowlist` — `src/mcp_coder/prompt_manager.py` entry removed (Step 1)

**Deleted** — none (no stubs, no re-exports; per the refactoring guide's "clean deletion").

### Implementation steps (each = exactly one commit)

- **Step 1 — Parsing module + its tests + allowlist removal.** Move the 3 parsing
  helpers to `prompt_parsing.py`; move the 3 parsing test classes to
  `test_prompt_parsing.py`; remove the allowlist entry. This move alone drops
  `prompt_manager.py` from 772 to ~668 lines (under 750), so the now-stale allowlist
  entry is removed **in the same commit** to keep the file-size check green.
- **Step 2 — Sources module + its tests.** Move the 4 source/loading helpers to
  `prompt_sources.py`; move the 4 source test classes to `test_prompt_sources.py`.
  `prompt_manager.py` finishes at ~450 lines.

Steps are independent in behavior (the two helper groups don't reference each other) but
are ordered so the allowlist obligation is discharged as soon as the file is compliant.

### TDD note

For a pure move-refactor, classic red→green TDD does not apply — no new logic is written.
The **existing test suite is the regression safety net**: it must pass before and after
each move, proving the relocation changed nothing. Each step therefore *relocates* its
mirror tests alongside the source and re-runs the full suite as the acceptance gate.

### Verification (run after every step — MCP tools)

1. `mcp__mcp-tools-py__run_format_code` — sweeps imports left unused by the move.
2. `git-tool compact-diff` — must show **only** import changes + new/deleted file
   headers. Any logic in the compact diff means something was modified during the move.
3. `mcp__mcp-workspace__check_file_size` — `prompt_manager.py` under 750 **and** off the
   allowlist.
4. `mcp__mcp-tools-py__run_lint_imports_check` (same-layer, no sub-layer expected),
   `run_pytest_check` (`-n auto` with the unit-test exclusion markers),
   `run_pylint_check`, `run_mypy_check` — all must pass.
5. `tach check` via Bash (no MCP equivalent).

### Constraints preserved
- Public API and all external import paths unchanged.
- Only private `_`-helpers move; whole functions relocate, only imports change.
- Same architecture layer → no import-linter sub-layer; module names
  (`prompt_sources.py`, `prompt_parsing.py`) don't collide with existing files.
- Test class distribution fixed at 4 / 4 / 3; new test files import the public API.
