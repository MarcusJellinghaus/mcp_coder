# Decisions Log: --execution-dir Feature

## Architectural Decisions

### 1. Separate Utility Function (Question 1)
**Decision:** Create separate `resolve_execution_dir()` utility
**Rationale:** Keep `project_dir` and `execution_dir` resolution independent
**Alternative Considered:** Reuse `resolve_project_dir()` logic with generic function

### 2. Implementation Order (Question 2)
**Decision:** Update workflows (Step 7) before command handlers (Steps 3-4)
**Rationale:** Avoid temporary type errors by having workflow signatures ready when command handlers call them
**Original Plan:** Command handlers first, then workflows

### 3. Documentation Step (Question 3)
**Decision:** Keep Step 6 as separate documentation-focused step
**Alternative Considered:** Merge documentation into Step 5 or Step 7

### 4. Command Handler Steps (Question 4)
**Decision:** Keep Steps 3 & 4 separate (prompt/commit vs implement/create-plan/create-pr)
**Note:** Now ordered after workflow changes due to Decision #2

### 5. Type Conversion Strategy (Question 5)
**Decision:** Use `Path` in command handlers, convert to `str` at workflow layer
**Alternative Considered:** Use `str` throughout or `Path` throughout

### 6. Default Behavior for None (Question 6)
**Decision:** `resolve_execution_dir(None)` returns `Path.cwd()` explicitly
**Alternative Considered:** Pass `None` through to subprocess or default to `project_dir`

### 7. Error Handling Consistency (Question 7)
**Decision:** Match existing `resolve_project_dir()` error handling pattern
**Action Required:** Review existing pattern and apply consistently

### 8. Testing Strategy (Question 8)
**Decision:** Use pytest parametrize and focus on essential tests (KISS principle)
**Change:** Reduce test volume from ~700 lines, eliminate non-essential tests

### 9. Logging Strategy (Question 9)
**Decision:** Log execution directory once at command handler entry point only
**Original Plan:** Log at multiple layers (command, workflow, LLM interface)

### 10. Default Behavior Semantics (Question 10)
**Decision:** `execution_dir=None` means "use process CWD" (explicit control)
**Alternative Considered:** `None` = use `project_dir` for backward compatibility

### 11. Migration Concerns (Question 11)
**Decision:** No migration guide or breaking change concerns needed
**Rationale:** Feature is backward compatible by design

### 12. Windows Compatibility (Question 12)
**Decision:** No explicit Windows path handling needed
**Rationale:** `pathlib.Path` handles cross-platform automatically

### 13. MCP Config Precedence (Question 13)
**Decision:** `execution_dir` takes precedence for `.mcp.json` discovery
**Rationale:** Claude runs in `execution_dir`, so naturally discovers config there first

### 14. Integration Testing Approach (Question 14)
**Decision:** Keep Step 8 as single step with tests and fixes together
**Alternative Considered:** Split into 8a (tests + fixes) and 8b (final docs)

## New Step Order

Based on Decision #2:

1. Step 1: Add path resolution utility
2. Step 2: Update CLI argument parsing
3. Step 5: Update LLM interface layer (moved up)
4. Step 6: Update Claude provider documentation (moved up)
5. Step 7: Update workflow layers (moved up)
6. Step 3: Update command handlers - prompt/commit (moved down)
7. Step 4: Update command handlers - implement/create-plan/create-pr (moved down)
8. Step 8: Integration testing and documentation
