# Plan Review Log — Issue #813 (Run 2)

## Round 1 — 2026-04-19

**Findings**:
1. (Critical) Steps 2/3 can't produce independent clean commits — step 2 source changes break test @patch targets not updated until step 3
2. (Improvement) Missing `tach.toml` `depends_on` entries in step 5 — vague "verify with tach check" instead of explicit list
3. (Improvement) `.importlinter` layered_architecture inconsistent with `tach.toml` — shim on same layer as utils instead of below
4. (Informational) `__init__` symbol count stale (says 6, actually 10 of 29)
5. (Nit) Step 2 should note which files DON'T need changes — skipped (cosmetic)
6. (Informational) Architecture docs will become stale — skipped (out of scope)
7. (Nit) `test_git_encoding_stress.py` dead import should be definitive, not "check if used"

**Decisions**:
- Finding 1 → accepted: moved 7 test files from step 3 to step 2 (test @patch updates alongside source changes)
- Finding 2 → accepted: listed 6 modules needing `depends_on` for `mcp_workspace_git`
- Finding 3 → accepted: placed shim on separate layer below utils in layered_architecture
- Finding 4 → accepted: updated symbol count to "10 of 29"
- Finding 5 → skipped (cosmetic, plan is clear enough)
- Finding 6 → skipped (out of scope)
- Finding 7 → accepted: changed to definitive "unused in this file"

**User decisions**: None needed (all findings were straightforward).

**Changes**:
- step_2.md: Added principle note, added 7 test files section, updated algorithm and LLM prompt
- step_3.md: Reduced scope to remaining tests + delete old tests + smoke test, fixed is_git_repository ambiguity
- step_5.md: Listed explicit `depends_on` entries, fixed layered_architecture placement
- summary.md: Updated step descriptions, fixed symbol count

**Status**: committed

## Round 2 — 2026-04-19

**Findings**:
1. (Critical) Smoke test created twice — step 1 creates it, step 3 tries to add it again
2. (Improvement) `tests` module missing `depends_on` for `mcp_workspace_git` in tach.toml step 5
3. (Improvement) Contradictory `is_git_repository` instructions in step 2 algorithm vs note
4. (Improvement) `mcp_tools_py` layer inconsistency between importlinter (alongside utils) and tach.toml (below utils in shim_workspace)
5. (Nit) Summary missing `test_git_tool.py` from modified files list
6. (Informational) Step 2/3 restructuring verified correct — all @patch dependencies properly assigned
7. (Informational) Symbol counts and architecture changes verified consistent

**Decisions**:
- Finding 1 → accepted: removed duplicate smoke test from step 3, added note referencing step 1
- Finding 2 → accepted: added `tests` to tach.toml `depends_on` list (now 7 modules)
- Finding 3 → accepted: changed "Remove is_git_repository" to "Source from shim (keep in __all__)", fixed note
- Finding 4 → accepted: aligned importlinter layers with tach — both shims on same layer below utils
- Finding 5 → accepted: added `test_git_tool.py` to summary

**User decisions**: None needed.

**Changes**:
- step_2.md: Fixed is_git_repository algorithm step and note
- step_3.md: Removed duplicate smoke test section, updated algorithm and LLM prompt
- step_5.md: Added `tests` to depends_on list, aligned importlinter layers
- summary.md: Added test_git_tool.py to modified files

**Status**: committed

## Round 3 — 2026-04-19

**Findings**:
1. (Improvement) Step 5 "Update dependants" section doesn't match the 7-module list — only explicitly adds to `mcp_coder.utils`, dismisses `workflows` with "layer hierarchy handles it"
2. (Nit) Step 3 table misleading about `test_check_branch_status_pr_waiting.py` — imports are inside-method lazy imports, not module-level
3. (Nit) Summary `cli/utils.py` description says "(lazy import)" but file has both top-level and lazy imports

**Decisions**:
- Finding 1 → accepted: replaced with explicit 7-module list
- Finding 2 → accepted: clarified as inside-method lazy imports
- Finding 3 → accepted: simplified to "Import from shim"

**User decisions**: None needed.

**Changes**:
- step_5.md: Explicit 7-module list in "Update dependants"
- step_3.md: Clarified lazy import type for test_check_branch_status_pr_waiting.py
- summary.md: Fixed cli/utils.py description

**Status**: committed

## Round 4 — 2026-04-19

**Findings**:
1. (Improvement) Contradictory root `__init__.py` note — says to source `create_branch`/`push_branch` from shim in root `__init__.py`, but they're not there; also contradicts clarification paragraph about `utils/__init__.py`
2. (Improvement) `tests/cli/test_utils.py` phantom @patch in step 2 — actual patches use import-destination path; 3 patches DO reference `git_operations.branch_queries` but belong in step 3 (source module not deleted until step 4)

**Decisions**:
- Finding 1 → accepted: fixed note to only mention `is_git_repository` for root `__init__.py`
- Finding 2 → accepted: moved `test_utils.py` from step 2 to step 3 with correct @patch targets

**User decisions**: None needed.

**Changes**:
- step_2.md: Fixed root `__init__.py` note, removed test_utils.py from test table
- step_3.md: Added test_utils.py with correct @patch details, removed from "already handled" note

**Status**: pending commit
