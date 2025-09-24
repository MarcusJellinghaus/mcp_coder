# Refactor Formatters to Use Directory-Based Approach

## Objective
Refactor the existing Black and isort formatters to use directory-based formatting instead of individual file processing, aligning with Step 0 analysis findings and leveraging built-in tool capabilities.

## Problem Statement
The current implementation uses a custom `find_python_files()` function to discover Python files and processes them individually. This approach:
- Duplicates functionality already built into Black and isort
- Ignores tool-specific exclusions (.gitignore, pyproject.toml excludes)
- Adds unnecessary complexity and performance overhead
- Contradicts the documented Step 0 analysis findings

## Solution Approach
Simplify formatters to pass target directories directly to Black/isort tools, letting them handle:
- File discovery and filtering
- Exclusion patterns (.gitignore, pyproject.toml)
- Performance optimizations
- Incremental formatting decisions

Use single-phase execution (format directly, no separate check step) and parse tool output to determine which files were actually changed, maintaining the same API contract.

## Key Changes
- **Remove** `find_python_files()` and file-by-file processing loops
- **Simplify** formatter logic to single-phase directory-based commands
- **Eliminate** separate check functions (use format + parsing approach)
- **Add** output parsing to extract changed file lists
- **Focus** testing on 3-4 essential tests per step
- **Maintain** existing public API (`FormatterResult` structure unchanged)

## Benefits
- **65+ lines of code removed** from core formatters (includes eliminated check functions)
- **Eliminates custom file discovery complexity**
- **Single-phase execution** (simpler command flow)
- **Respects tool-native exclusions** (.gitignore, etc.)
- **Improved performance** (no Python-level file scanning)
- **Focused testing** (3-4 tests per step vs 6-7)
- **Aligns with documented analysis** from Step 0

## Implementation Scope
- **3 core files**: black_formatter.py, isort_formatter.py, utils.py
- **4 test files**: corresponding test files
- **Testing approach**: 15-20 focused tests (vs 30+ comprehensive)
- **Risk level**: Low (simplification, maintaining API contract)

## Success Criteria
- All existing tests pass with updated expectations
- Same public API behavior (`FormatterResult` unchanged)
- Pylint, pytest, and mypy checks pass
- Formatters respect .gitignore and tool exclusions
- Performance improved (no custom file scanning)
