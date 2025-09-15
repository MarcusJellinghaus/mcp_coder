# Implementation Decisions Log

## Overview
This document captures key decisions made during the git commit feature planning discussion.

## Core API Decisions

### **1. Scope Simplification** ✅
**Decision**: Keep implementation simple for initial version
- Focus on core git commit functionality
- Defer advanced features (dry-run, complex workflows)
- Build foundation that can be extended later

### **2. Return Data Structure** ✅
**Decision**: Start with simple, extensible return structure
```python
CommitResult = {
    "success": bool,
    "commit_hash": str | None,  # Short hash like "a1b2c3d"
    "error": str | None
}
```
**Rationale**: 
- Easier to implement and test initially
- Can extend with more fields later without breaking changes
- Most use cases need success/failure and commit hash

### **3. Function Design Philosophy** ✅
**Decision**: Split into separate, focused functions instead of complex workflow function
- **Rejected**: One complex `commit_workflow()` with many parameters
- **Chosen**: Separate functions for different use cases

**Rationale**: 
- Each function has one clear purpose
- Easier to test individual pieces
- More git-aligned approach

### **4. Git Staging Approach** ✅
**Decision**: Provide both manual staging control and auto-staging convenience
```python
# Manual staging workflow
stage_specific_files([file1, file2], project_dir)
commit_staged_files(message, project_dir)

# Auto-staging convenience
commit_all_changes(message, project_dir)  # Stages everything automatically
```
**Rationale**: 
- Supports both simple and complex use cases
- Matches git's mental model
- Provides convenience without hiding the staging concept

### **5. Status Information Structure** ✅
**Decision**: Structured return for unstaged changes
```python
get_unstaged_changes(project_dir) -> {
    "modified": list[str],    # Files you changed
    "untracked": list[str]    # New files
}
```
**Rationale**: 
- Different meanings require different user decisions
- Matches how `git status` presents information
- Users can combine lists if they want all changes

### **6. API Function Set** ✅
**Decision**: Final API includes these functions:
```python
# Status functions
def get_staged_changes(project_dir: Path) -> list[str]
def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]

# Staging functions  
def stage_specific_files(files: list[Path], project_dir: Path) -> bool
def stage_all_changes(project_dir: Path) -> bool

# Commit functions
def commit_all_changes(message: str, project_dir: Path) -> CommitResult
def commit_staged_files(message: str, project_dir: Path) -> CommitResult

# Foundation (from p_fs)
def is_git_repository(project_dir: Path) -> bool
def is_file_tracked(file_path: Path, project_dir: Path) -> bool
```

### **7. Convenience Function Addition** ✅
**Decision**: Add `stage_all_changes()` as wrapper function
- Calls `get_unstaged_changes()` then `stage_specific_files()`
- Provides convenience while reusing core functions
- Maintains consistency in API design

### **8. Function Removal Decision** ✅
**Decision**: Remove `commit_specific_files()` function
**Rationale**: 
- Stay closer to git reality (stage then commit)
- Avoid duplication with existing workflow
- Users do: `stage_specific_files()` → `commit_staged_files()`
- More explicit and git-aligned

### **9. Error Handling Style** ✅
**Decision**: Return `False`/`None` on errors, don't raise exceptions
- Functions return boolean success indicators
- Commit functions return result dict with error field
- Log errors appropriately but don't crash calling code

## Implementation Approach

### **Deferred Features** ⏳
- Dry-run/preview mode
- Complex status reporting (before/after comparisons)  
- Advanced workflow parameters
- Commit message validation
- Git hooks integration
- Path validation beyond basic existence checks
- Performance optimizations for large repositories
- Merge conflict detection and resolution
- Branch management operations
- Remote repository operations (push/pull)
- Commit signing and GPG integration

### **Simplified Step Count** ✅
**Decision**: Reduce from 7 steps to 6 steps
- Remove complex workflow step
- Focus on core functionality
- Cleaner implementation path

### **Test-Driven Development** ✅
**Decision**: Use TDD for all new functionality
- Write tests before implementation
- Use existing p_fs tests as reference patterns
- Comprehensive error case testing

## Quality & Maintenance

### **Extensibility Design** ✅
- Simple return structures can be extended
- API functions are focused and composable
- Foundation supports adding advanced features later

### **Risk Reduction** ✅
- Simplified scope reduces implementation risk
- Proven foundation code from p_fs
- Git-aligned API reduces user confusion

## Recent Updates (September 2025)

### **10. Advanced Features Deferral** ✅
**Decision**: Expanded list of deferred features for v1.0
**Added to Deferred List**:
- Path validation beyond basic existence checks
- Performance optimizations for large repositories
- Merge conflict detection and resolution
- Branch management operations
- Remote repository operations (push/pull)
- Commit signing and GPG integration

**Rationale**: 
- Focus on core commit workflow for initial release
- Reduce implementation complexity and testing burden
- Ensure solid foundation before adding advanced features
- Most users need simple local commit functionality first

### **11. API Simplification Confirmation** ✅
**Decision**: Confirmed removal of `commit_specific_files()` function
**Rationale**:
- Avoids API duplication - same result achieved with `stage_specific_files()` → `commit_staged_files()`
- Keeps API focused on git's actual workflow
- Reduces testing complexity
- Makes user intent more explicit

### **12. Error Handling Standardization** ✅
**Decision**: Establish consistent error handling patterns
- Status functions: Return empty results on errors (list/dict)
- Staging functions: Return `False` on errors
- Commit functions: Return `{"success": False, "error": "message"}`
- All functions: Log errors appropriately but don't crash calling code

**Rationale**:
- Predictable behavior across all functions
- Calling code can handle errors gracefully
- Consistent with existing MCP Coder patterns

### **13. Plan Revision Discussion** ✅
**Decision**: Revised implementation plan based on review feedback
**Changes Made**:
- Keep `CommitResult` dictionary structure for structured error handling
- Maintain all 7 granular functions for maximum flexibility
- Add `get_full_status()` function for comprehensive status in one call
- Increase step granularity: 6 steps → 12 steps for better TDD workflow
- Merge test & implement phases into single steps
- Focus on behavior over implementation details in step descriptions
- Add more detailed integration testing requirements

**Rationale**:
- CommitResult provides calling code access to error details, not just logs
- Granular functions allow users to get exactly what they need
- get_full_status() provides efficiency option for comprehensive status
- Smaller steps align with KISS + TDD + incremental development principles
- Combined test/implement steps maintain TDD rhythm while reducing step overhead

---

**Last Updated**: September 15, 2025
**Status**: Decisions Finalized ✅
