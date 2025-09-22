# Project Plan Decisions

## Overview
This document records the decisions made during project plan review to simplify the Code Formatters Implementation.

## Key Simplification Decisions

### 1. Data Models (Step 1)
**Decision:** Use minimal `FileChange` data structure
- **Chosen:** Option A - Just `{file_path, had_changes}`
- **Rationale:** KISS principle - avoid unnecessary complexity of hashes and diffs
- **Impact:** Significantly simplified change detection logic

### 2. isort Implementation (Step 4)
**Decision:** Use isort's Python API directly
- **Chosen:** Option A - Use `isort.api.sort_file()` directly
- **Rationale:** isort API returns change status, eliminating need for complex subprocess + change detection
- **Impact:** Much cleaner implementation, fewer dependencies on utils

### 3. Shared Utilities (Step 5)
**Decision:** Keep utilities minimal
- **Chosen:** Option A - Only `get_python_files()` and basic path operations
- **Rationale:** With simplified data models and direct isort API, most complex utilities become unnecessary
- **Impact:** Reduced code complexity and maintenance burden

### 4. Implementation Steps Structure
**Decision:** Keep formatter steps separate
- **Chosen:** Option B - Separate steps for Black (Step 3) and isort (Step 4)
- **Rationale:** Easier debugging and testing, even with simplified approach
- **Impact:** Maintained clear separation of concerns

### 5. Testing Strategy
**Decision:** Focused testing approach
- **Chosen:** Option A - Core functionality + key integration tests, minimal test data
- **Rationale:** Avoid over-engineering test suites that slow development
- **Impact:** Faster development cycle, more maintainable tests

### 6. Dependency Management
**Decision:** Keep flexible version ranges
- **Chosen:** Option A - `black>=23.0.0`, `isort>=5.12.0`
- **Rationale:** Allows updates without breaking changes, easier maintenance
- **Impact:** No additional version management complexity

### 7. Configuration Conflict Handling
**Decision:** Simple warning for conflicts
- **Chosen:** Option B - Warn if line-length differs (~10 lines of code)
- **Rationale:** KISS principle - help users without complex validation logic
- **Impact:** Minimal added complexity, helpful user feedback

### 8. Error Handling Strategy
**Decision:** Fail fast approach
- **Chosen:** Option A - Let exceptions bubble up, stop on any error
- **Rationale:** Simplest implementation, clear and predictable behavior
- **Impact:** Minimal error handling code, straightforward user experience

### 9. API Design
**Decision:** Provide both individual and combined functions
- **Chosen:** Option B - Both `format_with_black()`, `format_with_isort()`, and `format_code()`
- **Rationale:** Maximum flexibility for users while maintaining clean API
- **Impact:** Slightly more code but much more flexible interface

## Technical Impact Summary

**Removed Complexity:**
- File content hashing and diff generation
- Complex change detection algorithms
- Extensive error handling and recovery logic
- Over-engineered utility functions
- Comprehensive test hierarchies

**Simplified Approach:**
- Direct API usage for isort (vs subprocess + change detection)
- Modification time-based change detection for Black
- Fail fast error handling
- Minimal shared utilities
- Focused testing on core functionality

**Maintained Features:**
- Full functionality for both Black and isort formatting
- Configuration reading from pyproject.toml
- Detailed result reporting
- Both individual and combined formatter APIs
- Integration test capabilities

## Result
The simplified plan maintains all core objectives while reducing implementation complexity by approximately 40-50%, focusing on essential functionality and following KISS principles throughout.
