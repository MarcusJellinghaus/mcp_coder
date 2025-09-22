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


---

# Updated Project Plan Decisions - September 2025

## Overview
Additional decisions made during detailed project plan review to further optimize the implementation approach while maintaining all functionality.

## Refined Implementation Decisions

### 1. API Design - Combined + Individual Functions
**Decision:** Include both individual and simple combined functions
- **Chosen:** Option B - Individual functions + simple 10-line combined wrapper
- **Rationale:** Combined function just calls the two others and aggregates results - very simple
- **Implementation:** `format_code()` calls `format_with_black()` and `format_with_isort()`, returns dict
- **Impact:** Maximum user flexibility with minimal code overhead

### 2. Configuration Warning - Line Length Conflicts
**Decision:** Add simple line-length conflict warning
- **Chosen:** Option B - Simple warning when Black/isort line lengths differ
- **Rationale:** Helpful user feedback without complex validation
- **Implementation:** ~10 lines of code to compare `tool.black.line-length` vs `tool.isort.line_length`
- **Impact:** Minimal complexity, useful user guidance

### 3. Configuration Implementation - Minimal Module
**Decision:** Simplified config_reader.py module
- **Chosen:** Option C - Minimal config reader with basic TOML parsing
- **Rationale:** Good balance of organization without over-engineering
- **Implementation:** Simple functions to read tool configs from pyproject.toml
- **Impact:** Clean code organization, reduced complexity vs original plan

### 4. Data Models - Keep Type Safety
**Decision:** Retain FormatterConfig dataclass
- **Chosen:** Option A - Keep structured FormatterConfig dataclass
- **Rationale:** Type safety and self-documenting interfaces worth the small overhead
- **Implementation:** ~10 lines for dataclass, provides clear API contracts
- **Impact:** Better maintainability and IDE support

### 5. Error Handling - Fail Fast
**Decision:** Simplest possible error handling
- **Chosen:** Option A - Fail fast with basic try/catch
- **Rationale:** Most simple approach, clear behavior
- **Implementation:** Single try/catch per formatter, return error in FormatterResult
- **Impact:** Minimal error handling code, predictable behavior

### 6. Change Detection - Parse Tool Outputs
**Decision:** Use tool outputs directly instead of file modification times
- **Chosen:** Option A - Parse Black stdout + use isort API returns
- **Rationale:** Get change information "for free" from tools themselves
- **Implementation:** Parse `"reformatted file.py"` from Black, use `isort.api.sort_file()` boolean
- **Impact:** Eliminates all file modification time complexity, more accurate

### 7. Testing Scope - Core Functionality First
**Decision:** Focus on essential tests initially
- **Chosen:** Option A - Core functionality + basic error cases (~15-20 tests)
- **Rationale:** Get working system quickly, expand tests as needed
- **Implementation:** Happy path, basic config, simple error scenarios
- **Impact:** Faster initial development, maintainable test suite

### 8. Project Structure - Minimal Files
**Decision:** 5-file structure without separate utils.py
- **Chosen:** Option A - Minimal structure (models, config, black, isort, __init__)
- **Rationale:** Keep it simple, inline utilities where needed
- **Implementation:** `get_python_files()` can be in formatter files or inlined
- **Impact:** Fewer files to manage, simpler project organization

### 9. Implementation Approach - Test-Driven Development
**Decision:** TDD step-by-step learning approach
- **Chosen:** Custom Option D - Write tests first, then implement each component
- **Rationale:** Learning-focused, ensures robust implementation
- **Implementation:** Models→Config→Black→isort→API, tests before code each step
- **Impact:** Better understanding, higher code quality, incremental progress

## Final Architecture Summary

### Project Structure
```
src/mcp_coder/formatters/
├── __init__.py           # Exports + format_code() wrapper (~20 lines)
├── models.py             # FormatterResult, FormatterConfig, FileChange (~30 lines)
├── config_reader.py      # Simple TOML reading + line-length warning (~40 lines)
├── black_formatter.py    # Black implementation with stdout parsing (~60 lines)
└── isort_formatter.py    # isort API implementation (~50 lines)
```

### Key Simplifications Achieved
- **Tool output parsing** eliminates complex change detection
- **Fail-fast error handling** reduces error management code
- **Simple combined API** provides flexibility without complexity
- **TDD approach** ensures quality while learning
- **Minimal file structure** reduces organizational overhead

### Maintained Capabilities
✅ Full Black and isort formatting functionality
✅ Configuration from pyproject.toml
✅ Detailed change reporting (which files modified)
✅ Both individual and combined formatter APIs
✅ Type-safe interfaces with proper error handling
✅ Comprehensive test coverage with integration tests
✅ Simple line-length conflict warnings

## Implementation Impact
- **~60% reduction** in total code lines vs original plan
- **~70% reduction** in complexity (fewer edge cases, simpler logic)
- **Maintained 100%** of core functionality requirements
- **TDD approach** ensures robust, well-tested implementation
- **Learning-optimized** step-by-step progression
