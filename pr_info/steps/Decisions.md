# Implementation Decisions

This document tracks decisions made during the planning review process.

## Decision Log

### 1. Template Selection Logic (Question 1)
**Decision:** Use dictionary-based mapping approach  
**Rationale:** Cleaner, more maintainable, less repetitive (DRY principle), easier to extend for new OS types  
**Alternative considered:** Nested if-else approach (initially chosen, then reconsidered)  
**Status:** Approved (Updated after review discussion - Question 4)

### 2. Test Coverage for dispatch_workflow() (Question 2)
**Decision:** Existing test coverage is sufficient  
**Rationale:** No additional test needed for dispatch_workflow()  
**Status:** Approved

### 3. Windows Environment Variable Documentation (Question 3)
**Decision:** Add comment next to Windows templates explaining `%VENV_BASE_DIR%`  
**Detail:** The Jenkins pipeline should set this variable  
**Location:** Step 1 - as comments in template constants  
**Status:** Approved

### 4. MCP Config File Naming (Question 4)
**Decision:** Standardize to `.mcp.json` for both Windows and Linux  
**Change:** Linux templates currently use `.mcp.linux.json`, will be updated to `.mcp.json`  
**Rationale:** Consistency and simplicity  
**Status:** Approved

### 5. Git Operations Approach (Question 5)
**Decision:** Windows approach (Jenkins handles git) is the better pattern  
**Future work:** Linux templates will be updated later to match this approach  
**Rationale:** Cleaner separation of concerns - Jenkins handles checkout  
**Status:** Approved (Windows implementation now, Linux update future)

### 6. Error Message Improvements (Question 6)
**Decision:** Make `executor_os` validation case-insensitive  
**Implementation:**
  - Accept "Windows", "WINDOWS", "Linux", "LINUX", etc.
  - Normalize to lowercase in `load_repo_config()`
  - Error message shows normalized value for simplicity (KISS principle)
**Status:** Approved (Error message format updated after review discussion - Question 12)

### 7. Integration Testing (Question 7)
**Decision:** Unit tests are sufficient for Step 5  
**Rationale:** Manual validation will cover integration scenarios  
**Status:** Approved

### 8. Field Rename: executor_test_path → executor_job_path (Question 8-9)
**Decision:** Rename field to `executor_job_path` (breaking change)  
**Scope:**
  - Config field: `executor_test_path` → `executor_job_path`
  - Jenkins parameter: `EXECUTOR_TEST_PATH` → `EXECUTOR_JOB_PATH`
**Backward compatibility:** None - users must update configs  
**Rationale:** Better naming clarity - this is a Jenkins job path, not just a test path  
**Implementation:** Include in Step 2 (config loading/validation)  
**Status:** Approved

### 9. Old Field Name Detection (Review Discussion - Question 2)
**Decision:** No special detection for old field name  
**Rationale:** Keep it simple - standard "missing field" error is sufficient  
**Alternative considered:** Add validation to detect `executor_test_path` and provide helpful migration error  
**Status:** Approved

### 10. Test Duplication Reduction (Review Discussion - Question 5)
**Decision:** Use pytest parametrized tests for template selection tests  
**Rationale:** Reduces code duplication, standard pytest pattern, easier to maintain  
**Implementation:** Step 3 tests will use `@pytest.mark.parametrize`  
**Status:** Approved

### 11. Config Template Comments (Review Discussion - Question 8)
**Decision:** Remove "RENAMED from..." comments from final user-facing config template  
**Rationale:** Clean template - these are implementation notes, not user documentation  
**Status:** Approved

### 12. Step 5 Validation Checklist (Review Discussion - Question 10)
**Decision:** Streamline checklist to integration-level validation only  
**Rationale:** Remove redundant unit-level items already covered in Steps 2-3  
**Status:** Approved

### 13. Rollback Plan (Review Discussion - Question 11)
**Decision:** Remove rollback plan section from README  
**Rationale:** Not needed for this implementation  
**Status:** Approved

### 14. Windows Environment Variable Documentation (Review Discussion - Question 7)
**Decision:** Keep minimal documentation - comment in template code is sufficient  
**Rationale:** Jenkins admins will know how to set environment variables  
**Alternative considered:** Add dedicated Jenkins configuration section  
**Status:** Approved

### 15. Template Documentation Duplication (Review Discussion - Question 9)
**Decision:** Keep templates in both DATA and Implementation Steps sections  
**Rationale:** Helpful to see templates in context during implementation  
**Status:** Approved

### 16. Test Implementation Detail Level (Review Discussion - Question 13)
**Decision:** Keep detailed test code with full mocking in step files  
**Rationale:** Helps implementers (especially LLMs) get it exactly right  
**Status:** Approved

## Summary of Key Changes

1. **Dictionary-based template selection** - Cleaner and more maintainable
2. **Parametrized tests** - Reduces test duplication in Step 3
3. **Case-insensitive OS validation** - More user-friendly
4. **Field renaming** - Breaking change for clarity (`executor_job_path`)
5. **MCP config standardization** - Use `.mcp.json` everywhere
6. **Documentation improvements** - Add VENV_BASE_DIR comments
7. **Git operations** - Windows approach is preferred (Jenkins handles it)
8. **Streamlined validation checklist** - Focus on integration-level checks
