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


---

# Step 0 Analysis Integration Decisions - September 23, 2025

## Overview
Decisions made during project plan revision to integrate insights from completed Step 0 analysis, resulting in ultra-simplified implementation with proven patterns.

## Key Insights from Step 0 Analysis

### Universal Exit Code Pattern
- **Discovery:** Both Black and isort use identical exit code conventions
  - Exit 0 = no changes needed
  - Exit 1 = changes were made/needed
  - Exit 123+ = syntax/other errors
- **Impact:** Eliminates need for complex change detection mechanisms

### Reliable CLI Integration Patterns
- **Discovery:** Both tools provide consistent, parseable output
- **Black:** "reformatted file.py" in stdout when changes made
- **isort:** "Fixing file.py" in stdout when changes made
- **Impact:** Simple string parsing sufficient for change detection

### Configuration Reading Strategy
- **Discovery:** Both tools read pyproject.toml consistently
- **Pattern:** Simple tomllib reading works reliably
- **Impact:** No need for complex configuration management

## Major Architectural Simplifications Based on Analysis

### 1. Change Detection Strategy
**Decision:** Use exit codes instead of file modification tracking
- **Chosen:** Universal exit code pattern (0=no changes, 1=changes needed)
- **Rationale:** Step 0 analysis proved this is 100% reliable for both tools
- **Implementation:** `result.returncode == 1` indicates changes needed
- **Impact:** Eliminates all complex file tracking, timestamps, and modification detection

### 2. CLI Command Patterns
**Decision:** Use proven command patterns from analysis
- **Chosen:** Two-phase approach - check first, then format if needed
- **Rationale:** Analysis shows this is most reliable approach
- **Implementation:** 
  - `black --check {file}` → format only if exit code 1
  - `isort --check-only {file}` → sort only if exit code 1
- **Impact:** Prevents unnecessary file modifications, more predictable behavior

### 3. Output Parsing Strategy
**Decision:** Parse tool stdout directly for change detection
- **Chosen:** String parsing patterns discovered in analysis
- **Rationale:** Tools provide reliable, parseable output indicating changes
- **Implementation:**
  - Black: Parse "reformatted {filename}" messages
  - isort: Parse "Fixing {filename}" messages
- **Impact:** No need for file discovery or modification time tracking

### 4. Configuration Reading Approach
**Decision:** Inline configuration reading based on analysis patterns
- **Chosen:** Simple tomllib reading in each formatter (~10 lines each)
- **Rationale:** Analysis shows this is sufficient and reliable
- **Implementation:** 
```python
def read_tool_config(tool_name: str) -> Dict[str, Any]:
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get(tool_name, {})
```
- **Impact:** Eliminates need for separate config module, each formatter self-contained

### 5. File Discovery Strategy
**Decision:** Let tools handle their own file discovery
- **Chosen:** Pass directories to tools, they handle file filtering
- **Rationale:** Analysis shows tools handle .gitignore, exclusions, and edge cases perfectly
- **Implementation:** Tools scan directories and report only files they actually modify
- **Impact:** Eliminates all custom file discovery logic, more reliable and comprehensive

### 6. Tool Integration Consistency
**Decision:** Use CLI for both tools consistently
- **Chosen:** Both Black and isort via CLI with identical patterns
- **Rationale:** Analysis shows both tools provide identical integration patterns
- **Implementation:** Same check-then-format approach for both tools
- **Impact:** Uniform implementation, easier to maintain and understand

### 7. Error Handling Strategy
**Decision:** Use exit codes for error detection
- **Chosen:** Standard subprocess error handling based on analysis
- **Rationale:** Analysis documents exact error patterns for both tools
- **Implementation:**
  - Exit 0: Success (no changes or changes applied)
  - Exit 1: Changes needed/applied
  - Exit 123+: Syntax errors or tool failures
- **Impact:** Clear, reliable error detection and handling

### 8. Ultra-Simplified Architecture
**Decision:** 3-file structure based on analysis simplifications
- **Chosen:** Only `__init__.py`, `black_formatter.py`, `isort_formatter.py`
- **Rationale:** Analysis eliminates need for separate models, config, and utility modules
- **Implementation:** 
  - `__init__.py`: FormatterResult dataclass + API functions (~50 lines)
  - `black_formatter.py`: Black integration + inline config (~45 lines)
  - `isort_formatter.py`: isort integration + inline config (~40 lines)
- **Impact:** ~135 total lines vs original 400+ lines (66% reduction)

### 9. Line-Length Conflict Detection
**Decision:** Simple warning based on analysis findings
- **Chosen:** Compare Black line-length vs isort line_length
- **Rationale:** Analysis shows this is most common configuration conflict
- **Implementation:** Read both configs, warn if line lengths differ
- **Impact:** Helpful user guidance with minimal complexity (~10 lines)

### 10. Test Strategy Enhancement
**Decision:** Use analysis patterns for realistic testing
- **Chosen:** Test with code samples from Step 0 analysis
- **Rationale:** Analysis provides proven problematic code samples
- **Implementation:** Use actual unformatted code and unsorted imports from analysis
- **Impact:** More realistic and comprehensive test coverage

### 11. Implementation Confidence
**Decision:** Use proven patterns from analysis throughout
- **Chosen:** Apply all discovered patterns and code examples from Step 0
- **Rationale:** Analysis eliminates guesswork and provides working examples
- **Implementation:** Direct application of analysis findings in each step
- **Impact:** Much higher implementation confidence and reliability

### 12. Development Approach
**Decision:** Enhanced TDD with analysis backing
- **Chosen:** Write tests first using analysis findings, then implement
- **Rationale:** Analysis provides concrete test scenarios and expected behaviors
- **Implementation:** Each step starts with comprehensive tests based on analysis
- **Impact:** Higher quality implementation with proven test cases

## Analysis-Driven Architecture Summary

### Ultra-Simplified Project Structure
```
src/mcp_coder/formatters/
├── __init__.py           # FormatterResult + API functions (~50 lines)
├── black_formatter.py    # Black CLI + inline config (~45 lines)
└── isort_formatter.py    # isort CLI + inline config (~40 lines)
```
**Total: ~135 lines** (vs original estimate of 400+ lines)

### Analysis-Based Simplifications
- ✅ **Exit code change detection** - No file modification tracking needed
- ✅ **Tool output parsing** - Simple string patterns sufficient
- ✅ **Inline configuration** - No separate config module needed
- ✅ **Tool-handled file discovery** - No custom file scanning needed
- ✅ **Consistent CLI patterns** - Same approach for both tools
- ✅ **Proven error handling** - Standard subprocess patterns

### Eliminated Components (Due to Analysis)
- ❌ Complex change detection algorithms → Exit codes
- ❌ File modification time tracking → Tool output parsing
- ❌ Separate configuration modules → Inline reading
- ❌ Custom file discovery utilities → Tool-handled scanning
- ❌ isort Python API complexity → Consistent CLI approach
- ❌ FileChange dataclass → Simple string lists
- ❌ FormatterConfig dataclass → Simple dictionaries

### Core Features Maintained
✅ **Full functionality** - Black and isort formatting with change detection
✅ **Configuration support** - Read from pyproject.toml with inline patterns
✅ **Change reporting** - Detailed file-level change information
✅ **Flexible API** - Individual and combined formatter functions
✅ **Conflict detection** - Line-length mismatch warnings
✅ **Quality assurance** - TDD approach with analysis-backed tests
✅ **Integration ready** - Real tool execution with comprehensive testing

## Implementation Confidence

### High Confidence Areas (From Analysis)
- **Tool behavior patterns** - Extensively tested and documented
- **Command-line interfaces** - Proven working examples
- **Configuration reading** - Validated TOML parsing patterns
- **Error scenarios** - Known error conditions and responses
- **Change detection** - Reliable exit code and output patterns

### Implementation Impact
- **75% complexity reduction** through analysis-driven simplification
- **66% code reduction** (~135 lines vs 400+ originally estimated)
- **100% functionality preservation** with higher reliability
- **Faster development** due to proven patterns and reduced scope
- **Higher quality** through TDD with realistic test scenarios

## Ready for Implementation
Step 0 analysis provides concrete, proven patterns for immediate implementation of Steps 1-5 with high confidence and minimal risk.
