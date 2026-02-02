# Decisions Log

## Decision 1: Shared Helper Location

**Date:** 2026-02-02

**Question:** Where should `_get_vscodeclaude_config()` be defined?

**Options Considered:**
- A) Keep as planned - Each module has its own lookup logic (slight duplication)
- B) Put `_get_vscodeclaude_config()` in `issues.py` - Single source, both modules import from it
- C) Put it in `workspace.py`, have `helpers.py` import from there

**Decision:** Option B - Add `_get_vscodeclaude_config()` to `issues.py`

**Rationale:**
- DRY - One helper function instead of duplicated logic in two files
- Natural home - `issues.py` already owns `_load_labels_config()`, so config-related helpers belong there
- Easier maintenance - If lookup logic ever changes, fix it in one place

**Impact on Plan:**
- Step 2: Add `_get_vscodeclaude_config()` alongside priority extraction work
- Step 3: Import from `issues.py` instead of defining own lookup
- Step 4: Import from `issues.py` instead of inline lookup logic
