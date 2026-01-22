# Issue #314: Improve Formatter Error Handling

## Summary

Add debug logging for stderr output and early exit on formatter failure to improve debugging experience when formatters fail (e.g., Black exits with code 123 due to syntax error).

## Problem Statement

When formatters fail:
1. **Stderr output is lost** - Black's stderr (which shows WHICH file has the syntax error) is not logged
2. **Formatters continue after failure** - isort runs even when Black fails, wasting time
3. **Error timing is confusing** - errors are logged at the end, not when they occur

## Architectural / Design Changes

### Design Philosophy
- **Minimal changes**: Only add logging and early exit logic, no refactoring
- **KISS principle**: Use Python's built-in logging module consistently
- **Preserve existing behavior**: Error messages in `FormatterResult` remain unchanged

### Changes Overview

| Component | Change Type | Description |
|-----------|-------------|-------------|
| `black_formatter.py` | Enhancement | Add DEBUG logging for stderr on failure |
| `isort_formatter.py` | Enhancement | Add DEBUG logging for stderr on failure |
| `formatters/__init__.py` | Enhancement | Add early exit + INFO logging on failure |

### Logging Strategy
- **DEBUG level**: Stderr output from failed formatters (for developers debugging)
- **INFO level**: Formatter failure notification in `format_code()` (for visibility)

## Files to Modify

| File | Action | Lines Changed |
|------|--------|---------------|
| `src/mcp_coder/formatters/black_formatter.py` | Modify | ~5 lines |
| `src/mcp_coder/formatters/isort_formatter.py` | Modify | ~5 lines |
| `src/mcp_coder/formatters/__init__.py` | Modify | ~8 lines |
| `tests/formatters/test_black_formatter.py` | Modify | ~20 lines |
| `tests/formatters/test_isort_formatter.py` | Modify | ~20 lines |
| `tests/formatters/test_main_api.py` | Modify | ~25 lines |

## Data Flow

```
format_code()
    │
    ├── format_with_black()
    │   ├── Success → continue to next formatter
    │   └── Failure → log DEBUG stderr, return FormatterResult(success=False)
    │                      │
    │                      ▼
    │              log INFO "Black failed", break loop ◄── NEW
    │
    └── format_with_isort() ◄── Only runs if Black succeeded
        ├── Success → continue
        └── Failure → log DEBUG stderr, return FormatterResult(success=False)
                           │
                           ▼
                   log INFO "isort failed", break loop ◄── NEW
```

## Implementation Steps

| Step | Description | Files | Test-First |
|------|-------------|-------|------------|
| 1 | Add stderr debug logging to Black formatter | `black_formatter.py`, `test_black_formatter.py` | Yes |
| 2 | Add stderr debug logging to isort formatter | `isort_formatter.py`, `test_isort_formatter.py` | Yes |
| 3 | Add early exit on failure in format_code() | `__init__.py`, `test_main_api.py` | Yes |
