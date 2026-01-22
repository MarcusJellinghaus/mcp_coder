# Issue #314: Improve Formatter Error Handling

## Summary

Improve formatter error handling by:
1. Including stderr output in error messages (so users can see which file caused the error)
2. Adding DEBUG logging for full commands (for debugging complex issues)
3. Adding early exit on failure (don't run isort if Black fails)

## Problem Statement

When formatters fail:
1. **Stderr output is lost** - Black's stderr (which shows WHICH file has the syntax error) is not included in the error message
2. **Formatters continue after failure** - isort runs even when Black fails, wasting time
3. **Command details are hidden** - Full command with all flags isn't visible for debugging

## Architectural / Design Changes

### Design Philosophy
- **Minimal changes**: Only add logging and early exit logic, no refactoring
- **KISS principle**: Use Python's built-in logging module consistently
- **Better visibility**: Include stderr in error_message directly (not hidden behind DEBUG level)

### Changes Overview

| Component | Change Type | Description |
|-----------|-------------|-------------|
| `black_formatter.py` | Enhancement | Include stderr in error_message + DEBUG log for command |
| `isort_formatter.py` | Enhancement | Include stderr in error_message + DEBUG log for command |
| `formatters/__init__.py` | Enhancement | Add early exit + INFO logging on failure |

### Logging Strategy
- **DEBUG level**: Full command before execution (for debugging)
- **INFO level**: Formatter failure notification in `format_code()` (for visibility)
- **error_message**: Now includes stderr output (always visible in FormatterResult)

## Files to Modify

| File | Action | Lines Changed |
|------|--------|---------------|
| `src/mcp_coder/formatters/black_formatter.py` | Modify | ~15 lines |
| `src/mcp_coder/formatters/isort_formatter.py` | Modify | ~15 lines |
| `src/mcp_coder/formatters/__init__.py` | Modify | ~10 lines |
| `tests/formatters/test_black_formatter.py` | Modify | ~40 lines |
| `tests/formatters/test_isort_formatter.py` | Modify | ~40 lines |
| `tests/formatters/test_main_api.py` | Modify | ~60 lines |

## Data Flow

```
format_code()
    │
    ├── format_with_black()
    │   ├── _format_black_directory()
    │   │   └── logger.debug("Black command: %s", command)  ◄── NEW
    │   ├── Success → continue to next formatter
    │   └── Failure → return FormatterResult(error_message includes stderr)  ◄── IMPROVED
    │                      │
    │                      ▼
    │              log INFO "black formatting failed", break loop  ◄── NEW
    │
    └── format_with_isort()  ◄── Only runs if Black succeeded
        ├── _format_isort_directory()
        │   └── logger.debug("isort command: %s", command)  ◄── NEW
        ├── Success → continue
        └── Failure → return FormatterResult(error_message includes stderr)  ◄── IMPROVED
                           │
                           ▼
                   log INFO "isort formatting failed", break loop  ◄── NEW
```

## Implementation Steps

| Step | Description | Files | Test-First |
|------|-------------|-------|------------|
| 1 | Improve Black error handling + add debug logging | `black_formatter.py`, `test_black_formatter.py` | Yes |
| 2 | Improve isort error handling + add debug logging | `isort_formatter.py`, `test_isort_formatter.py` | Yes |
| 3 | Add early exit on failure in format_code() | `__init__.py`, `test_main_api.py` | Yes |

## Key Technical Detail

`subprocess.CalledProcessError` with 3-argument form stores output in `e.output`, not `e.stderr`:
```python
# Current code raises:
raise subprocess.CalledProcessError(result.return_code, command, result.stderr)
# The result.stderr becomes e.output, NOT e.stderr

# Solution - check both attributes:
stderr_output = getattr(e, "output", "") or getattr(e, "stderr", "") or ""
```
