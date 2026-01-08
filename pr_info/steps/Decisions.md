# Implementation Decisions

Decisions made during plan review discussion.

---

## Decision 1: Documentation Location

**Question**: Where to place the new label setup documentation?

**Options discussed**:
- A) Update existing file in-place (`docs/configuration/LABEL_WORKFLOW_SETUP.md`)
- B) Rename existing file (same folder, shorter name)
- C) Create new `docs/getting-started/LABEL_SETUP.md` directory structure

**Decision**: **C** - Create new `docs/getting-started/LABEL_SETUP.md`

**Additional action**: Update all references including `docs/configuration/CONFIG.md` (found via search).

---

## Decision 2: Reuse `resolve_project_dir`

**Question**: Should we copy `resolve_project_dir` or import from existing shared utility?

**Options discussed**:
- A) Import from existing `mcp_coder.workflows.utils` (no code duplication)
- B) Move to `cli/utils.py`
- C) Copy as planned (self-contained)

**Decision**: **A** - Import from existing `mcp_coder.workflows.utils`

---

## Decision 3: LLM Prompt Sections

**Question**: Should the verbose "LLM Prompt" sections in each step file be kept?

**Options discussed**:
- A) Remove LLM Prompt sections
- B) Keep LLM Prompt sections
- C) Move to separate file

**Decision**: **B** - Keep LLM Prompt sections in step files

---

## Decision 4: Test Migration Scope

**Question**: How thorough should the new `TestExecuteDefineLabels` class be?

**Options discussed**:
- A) Minimal (1-2 tests for wiring and exit codes)
- B) Comprehensive (multiple tests covering all scenarios)
- C) Skip entirely (rely on existing `TestApplyLabels`)

**Decision**: **A** - Minimal tests (1-2) focusing on basic wiring and exit codes

---

## Decision 5: `--log-level` Handling

**Question**: Should the `define-labels` subparser have its own `--log-level` argument?

**Options discussed**:
- A) Parent parser only (users use `mcp-coder --log-level DEBUG define-labels`)
- B) Both levels (allow both syntaxes)

**Decision**: **A** - Parent parser only (consistent with other commands)

---

## Decision 6: Error Handling Pattern

**Question**: Should `apply_labels` and `resolve_project_dir` use `sys.exit(1)` or raise exceptions?

**Options discussed**:
- A) Keep `sys.exit()` calls (simpler, existing behavior)
- B) Refactor to exceptions (cleaner CLI pattern)
  - B1) Refactor `apply_labels` only
  - B2) Full refactor including `resolve_project_dir`
    - B2a) Include in this plan
    - B2b) Separate issue
    - B2c) Partial (only some consumers)

**Decision**: **B2a** - Full refactor to exceptions, included in this plan

**Scope**: 
- Refactor `resolve_project_dir` in `workflows/utils.py` to raise `ValueError`
- Update `workflows/validate_labels.py` with try/except wrapper
- Update `tests/workflows/implement/test_core.py` to expect `ValueError`
- New `apply_labels` raises `RuntimeError` instead of `sys.exit(1)`

---

## Decision 7: Config File Fallback Behavior

**Question**: Should the CLI command require a local config or keep the fallback to bundled config?

**Options discussed**:
- A) Keep fallback behavior (local → bundled)
- B) Require local config

**Decision**: **A** - Keep fallback behavior

**Additional action**: Document both config file locations in the new documentation:
1. Local override: `project_dir/workflows/config/labels.json`
2. Bundled fallback: `mcp_coder/config/labels.json`

This ensures consistency since other components (`validate_labels.py`, `issue_stats.py`, coordinator) already use the same two-location config system.

---

## Decision 8: Clarify Duplicate `resolve_project_dir`

**Question**: Should Step 1 explicitly note that `workflows/define_labels.py` has its own duplicate copy of `resolve_project_dir` that will simply be deleted (not refactored)?

**Options discussed**:
- A) Yes, add a clarifying note to Step 1
- B) No, it's already implied since the file gets deleted in Step 5

**Decision**: **A** - Add clarifying note to Step 1

---

## Decision 9: Consolidate Refactoring in Step 1

**Question**: Should we move the `tests/workflows/implement/test_core.py` update from Step 3 to Step 1 so the refactoring is self-contained?

**Options discussed**:
- A) Yes, move to Step 1 (keeps refactoring self-contained, tests pass immediately)
- B) No, keep in Step 3 (groups all test changes together)

**Decision**: **A** - Move `test_core.py` update to Step 1

---

## Decision 10: Explicit Code Quality Checks

**Question**: Should each step's verification section explicitly include running code quality checks (pylint/pytest/mypy)?

**Options discussed**:
- A) Yes, add explicit reminder to each step's verification section
- B) No, it's already in CLAUDE.md - implementer should know

**Decision**: **A** - Add explicit code quality check reminders to each step

---

## Decision 11: Verification Checkpoint in Step 1

**Question**: Should Step 1 include an explicit verification checkpoint between the refactoring (Parts A+B) and the CLI command creation (Part C)?

**Options discussed**:
- A) Yes, add checkpoint (verify refactoring before proceeding)
- B) No, keep as continuous flow (simpler structure)

**Decision**: **A** - Add verification checkpoint after refactoring parts
