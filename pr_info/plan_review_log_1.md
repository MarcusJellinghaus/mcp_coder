# Plan Review Log — Run 1

**Issue:** #613 — Align launcher and install scripts with environment model
**Date:** 2026-03-29
**Branch:** 613-chore-align-launcher-and-install-scripts-with-environment-model

## Round 1 — 2026-03-29

**Findings:**
- **Critical**: Step 1 misses workspace server PYTHONPATH change from `${VIRTUAL_ENV}` to `${MCP_CODER_VENV_DIR}` (p_tools reference and environments.md both require this)
- **Critical**: Step 2 algorithm doesn't handle VIRTUAL_ENV already pointing to project env — would incorrectly treat project env as tool env
- **Improvement**: `where mcp-coder` can return multiple results; algorithm didn't specify first-result-only
- **Improvement**: Step ordering creates transient breakage (step 1 uses MCP_CODER_VENV_PATH before any launcher sets it)
- **Improvement**: MCP_CODER_VENV_DIR derivation not specified in step 2 algorithm
- **Improvement**: Step 4 behavioral change (editable → non-editable) not explicitly noted for existing users
- **Skip**: TASK_TRACKER.md empty — populated automatically at implementation time per planning principles
- **Skip**: setlocal scope — no change needed, positive observation
- **Skip**: Duplicate code across bat files — acceptable for batch scripts
- **Skip**: environments.md target state omission — out of scope
- **Skip**: DISABLE_AUTOUPDATER addition — positive confirmation
- **Skip**: Planning principles compliance — positive confirmation

**Decisions:**
- Finding 1 (PYTHONPATH): Accept — clearly needed per environments.md and p_tools reference
- Finding 2 (step ordering): Accept — add note acknowledging transient breakage (coordinator path still works)
- Finding 3 (where multi-result): Accept — clarify first-result-only in algorithm
- Finding 4 (VIRTUAL_ENV guard): Accept — algorithm bug, add same guard as step 3
- Finding 5 (TASK_TRACKER): Skip — auto-populated at implementation time
- Finding 7 (behavioral change): Accept — add note directing developers to reinstall_local.bat
- Finding 8 (VENV_DIR derivation): Accept — clarify in algorithm
- Findings 6, 9-12: Skip — observations only, no changes needed

**User decisions:** None required — all accepted findings were straightforward improvements.

**Changes:**
- `pr_info/steps/step_1.md`: Added PYTHONPATH as 3rd substitution, transient breakage note, updated LLM prompt
- `pr_info/steps/step_2.md`: Fixed VIRTUAL_ENV 3-way guard, first-result-only, MCP_CODER_VENV_DIR derivation
- `pr_info/steps/step_3.md`: Added first-result-only to where lookups
- `pr_info/steps/step_4.md`: Added behavioral change note
- `pr_info/steps/summary.md`: Updated step 1 description to "3-line edit"

**Status:** Committed
