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
- Two cohesive groups of private helpers move into **sibling modules** (siblings of each
  other, in a new sub-layer beneath `prompt_manager` — see the import-linter note below):
  - `prompt_sources.py` — path resolution + content loading (filesystem / package I/O).
  - `prompt_parsing.py` — pure markdown-string parsing (no I/O).
- The two helper groups are **independent siblings** (verified in code: no cross-calls
  between them). Both are consumed only by `prompt_manager.py`. `prompt_manager` **is**
  an explicit layer in the import-linter contract (`.importlinter` line 39:
  `mcp_coder.llm | mcp_coder.prompt_manager`, sitting above `mcp_coder.prompts` and
  `mcp_coder.utils`). The two new modules are **not yet** named in any contract, so they
  would float unconstrained. **APPROVED decision (Round 1):** add a NEW sub-layer
  BENEATH `prompt_manager` so both new modules are layer-enforced. Intended final layer
  block:
  ```
  mcp_coder.llm | mcp_coder.prompt_manager
  mcp_coder.prompt_sources | mcp_coder.prompt_parsing
  mcp_coder.prompts
  ```
  Rationale: `prompt_manager` imports both new modules (top-down dependency), so they
  must sit in a **lower** layer — they cannot be appended to line 39 with `|`, because
  same-line siblings may not import each other (that would break the contract). The two
  new modules are independent siblings of **each other** (no cross-calls), which matches
  the `|` on their new line. This `.importlinter` edit names BOTH new modules, so it can
  only be applied once both exist → it lands in **Step 2** (after `prompt_sources.py` is
  created). In Step 1, `prompt_parsing.py` exists but stays unlisted/floating
  temporarily — that is expected and fine. `run_lint_imports_check` must still PASS with
  the new sub-layer present.
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
- `src/mcp_coder/prompt_manager.py` — helpers removed; imports added; imports left unused
  by the move removed via `run_ruff_fix` (F401)
- `tests/test_prompt_manager.py` — drained test classes removed
- `.large-files-allowlist` — `src/mcp_coder/prompt_manager.py` entry removed (Step 1)
- `.importlinter` — add sub-layer `mcp_coder.prompt_sources | mcp_coder.prompt_parsing`
  beneath `prompt_manager` (Step 2)
- `tach.toml` — declare each new module (`mcp_coder.prompt_parsing` in Step 1,
  `mcp_coder.prompt_sources` in Step 2) as a `domain` `[[modules]]` entry and add each to
  `mcp_coder.prompt_manager`'s `depends_on`

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

1. `mcp__mcp-tools-py__run_ruff_fix` selecting **F401** — removes imports left unused by
   the move (`run_format_code` runs black + isort only; neither removes unused imports).
   An explicit manual removal of the named imports is an acceptable alternative.
2. `git-tool compact-diff` — must show **only** import changes + new/deleted file
   headers. Any logic in the compact diff means something was modified during the move.
3. `mcp__mcp-workspace__check_file_size` — `prompt_manager.py` under 750 **and** off the
   allowlist.
4. `mcp__mcp-tools-py__run_lint_imports_check` — must PASS with the new sub-layer
   (`mcp_coder.prompt_sources | mcp_coder.prompt_parsing`) present after Step 2;
   `run_pytest_check` (`-n auto` with the unit-test exclusion markers),
   `run_pylint_check`, `run_mypy_check` — all must pass.
5. `tach check` via Bash (no MCP equivalent). Both new modules must be declared in
   `tach.toml` (`prompt_parsing` in Step 1, `prompt_sources` in Step 2) as `domain`
   `[[modules]]`, with `prompt_manager` depending on each — otherwise the undeclared
   module folds into the root `mcp_coder`, and `prompt_manager → mcp_coder` combined with
   the root's existing dependency on `prompt_manager` forms a circular dependency that
   fails `tach check`. Sequencing asymmetry vs `.importlinter`: tach declares each module
   individually, so `tach.toml` is updated per-step (one module each), whereas the
   `.importlinter` sub-layer line names both modules and is therefore added once, in
   Step 2.

### Constraints preserved
- Public API and all external import paths unchanged.
- Only private `_`-helpers move; whole functions relocate, only imports change.
- `prompt_manager` is a named import-linter layer (`.importlinter`); a new sub-layer
  `mcp_coder.prompt_sources | mcp_coder.prompt_parsing` is added beneath it in Step 2 so
  the new modules are layer-enforced. Module names (`prompt_sources.py`,
  `prompt_parsing.py`) don't collide with existing files.
- Test class distribution fixed at 4 / 4 / 3; new test files import the public API.
