# Implementation Decisions

## Discussed and Agreed Decisions

### 1. Step Structure (Topic 1)
**Decision**: Keep steps 1-6 separate (granular approach)
**Rationale**: More granular commits and clearer progress tracking

### 2. Batch File (Topic 2)
**Decision**: Include `define_labels.bat` wrapper (Step 5)
**Rationale**: Consistency with existing workflow scripts

### 3. Integration Tests (Topic 3)
**Decision**: Skip integration tests - unit tests only
**Rationale**: Integration tests requiring GitHub tokens are fragile, slow, and often skipped in CI. Comprehensive unit test coverage is sufficient.

### 4. Test Architecture (Topic 3, continued)
**Decision**: Separation of concerns - pure `calculate_label_changes()` function + `apply_labels()` orchestrator
**Rationale**: 
- Pure function for business logic (easy to test, no mocking needed)
- Orchestrator handles side effects (API calls, minimal mocking)
- Fast, deterministic tests for all edge cases

### 5. Test Coverage (Topic 3, continued)
**Decision**: Include all edge cases:
- Empty repository (no labels)
- Partial match (5 of 10 labels exist)
- Error handling (GitHub API failures)
- Color format validation
**Rationale**: Comprehensive coverage ensures robustness

### 6. Error Handling Strategy (Topic 4)
**Decision**: Fail fast - exit immediately with code 1 on any error
**Rationale**: Clear failure indication, no silent errors

### 7. Dry-Run Mode (Topic 5)
**Decision**: Add `--dry-run` flag
**Rationale**: User-friendly preview of changes before applying

### 8. Label Color Validation (Topic 6)
**Decision**: Validate color format (6-char hex) before API calls
**Rationale**: Catch configuration errors early

### 9. Obsolete Label Detection (Topic 7)
**Decision**: Strict deletion - remove ANY `status-*` label not in WORKFLOW_LABELS
**Rationale**: Clean state enforcement, only defined labels allowed

### 10. Idempotency & API Call Optimization (Topic 8)
**Decision**: Skip API calls entirely for unchanged labels
**Rationale**: Efficient, truly idempotent, reduces API rate limit usage

### 11. Logging Detail Level (Topic 9)
**Decision**: Log each action at INFO level (not just summary)
**Format**: "Created: status-01:created", "Updated: status-05:plan-ready", etc.
**Rationale**: Detailed visibility of operations for debugging and confirmation

### 12. Test Data Structure (Topic 10)
**Decision**: Use tuples `(name, color, description)` like WORKFLOW_LABELS
**Rationale**: Consistency with constant definition

### 13. Initial Checks (Topic 11)
**Decision**: Use existing validation functions:
- `resolve_project_dir()` - validates `.git/` exists
- `LabelsManager.__init__()` - validates token and repo connection
**Rationale**: Leverage existing robust validation, no duplication

### 14. Constants Validation (Topic 11, continued)
**Decision**: No validation of hardcoded WORKFLOW_LABELS constants
**Rationale**: Trust hardcoded values, no runtime validation needed as values come from script, not user input

### 15. Non-Status Label Preservation (Topic 8)
**Decision**: Only `status-*` labels are managed; all other labels (e.g., `bug`, `enhancement`) are never touched
**Rationale**: Clear separation of concerns - script only manages workflow status labels

### 16. Color Validation Location (Review Topic 1)
**Decision**: Validate WORKFLOW_LABELS color format at module load
**Rationale**: Colors from hardcoded constants - catch errors immediately when script imports

### 17. Logging in Pure Function (Review Topic 2)
**Decision**: Only `apply_labels()` logs, `calculate_label_changes()` stays side-effect-free
**Rationale**: Maintain pure function principles - no side effects in business logic

### 18. Error Handling Flow (Review Topic 3)
**Decision**: Stop immediately on first API error (true fail-fast)
**Rationale**: Clean, predictable behavior - no partial state, matches Decision #6

### 19. Test Data Location (Review Topic 4)
**Decision**: Pytest fixtures in `test_define_labels.py` file
**Rationale**: Balance reusability and locality for mock data

### 20. Documentation Strategy (Review Topic 5)
**Decision**: Code comments and docstrings sufficient - no additional documentation step
**Rationale**: Keep plan focused, standard code documentation adequate

### 21. Test Count Specification (Review Topic 6)
**Decision**: 17+ total tests (8 pure function, 3 orchestrator, 4 CLI, 2 main)
**Rationale**: Accurate count for verification

### 22. Algorithm Numbering (Review Topic 7)
**Decision**: Add missing line: "Initialize result dict" as line 1 in calculate_label_changes
**Rationale**: Complete algorithm specification

### 23. Main Function Test Coverage (Review Topic 8)
**Decision**: 2 tests sufficient for main() (success, error)
**Rationale**: Underlying functions thoroughly tested separately

### 24. CLI Test Enumeration (Review Topic 9)
**Decision**: Keep concise - no explicit test enumeration in Step 3
**Rationale**: Consistency preference, tests obvious from context

### 25. Batch File Documentation (Review Topic 10)
**Decision**: No Windows-specific note needed
**Rationale**: .bat extension self-explanatory
