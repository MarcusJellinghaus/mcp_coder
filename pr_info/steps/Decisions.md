# Implementation Decisions

This document tracks decisions made during the planning review process.

## Decision Log

### 1. Template Selection Logic (Question 1)
**Decision:** Keep nested if-else approach  
**Rationale:** Explicit and easier to understand  
**Alternative considered:** Mapping dictionary approach  
**Status:** Approved

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
  - Error message shows original invalid value (e.g., "got 'MacOS'")
**Status:** Approved

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

## Summary of Key Changes

1. **Case-insensitive OS validation** - More user-friendly
2. **Field renaming** - Breaking change for clarity (`executor_job_path`)
3. **MCP config standardization** - Use `.mcp.json` everywhere
4. **Documentation improvements** - Add VENV_BASE_DIR comments
5. **Git operations** - Windows approach is preferred (Jenkins handles it)
