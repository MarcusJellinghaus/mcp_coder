# Issue #284: Migrate CI to uv and Display Tool Versions

## Overview

Migrate the CI pipeline from `pip` to `uv` for faster dependency installation and add version display for all tools to improve debugging when CI fails.

## Architectural / Design Changes

### No Architectural Changes Required

This issue involves **CI/CD configuration changes only**. No changes to:
- Source code (`src/`)
- Tests (`tests/`)
- Project structure
- Python dependencies (only how they're installed)

### Design Decisions

1. **KISS Principle**: Prepend version commands to existing matrix `cmd` fields using `&&` instead of adding new steps or matrix fields
2. **Single Environment Step**: One consolidated step for system/tool info instead of multiple steps
3. **Unified Dependency Installation**: Single `uv pip install --system ".[dev]"` replaces three pip commands

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| `.github/workflows/ci.yml` | Modified | Migrate to uv, add version display |

## Requirements Checklist

- [x] CI migrated from `pip` to `uv` using `astral-sh/setup-uv` action
- [x] Type stubs installed via `.[dev]` (dev includes types)
- [x] Environment info step added at the start of `test` and `architecture` jobs
- [x] Each tool check shows its version before execution
- [x] uv version displayed in environment info
- [x] No functional changes to existing checks (same tools, same flags)

## Implementation Summary

### Step 1: Migrate to uv and Update Dependencies
- Add `astral-sh/setup-uv@v4` action to both jobs
- Replace pip installation with `uv pip install --system ".[dev]"`

### Step 2: Add Environment Info and Tool Versions
- Add environment info step to both jobs
- Prepend `<tool> --version &&` to each matrix command

## Benefits

- **Faster CI**: uv is significantly faster than pip
- **Better type checking**: Type stubs ensure mypy has complete type information
- **Easier debugging**: Version info helps identify version-specific failures
- **Better reproducibility**: Clear audit trail of exact versions used

## Testing Strategy

Since this is a CI configuration change:
- **No unit tests required** - this is infrastructure configuration
- **Validation**: Create PR and verify CI passes with new configuration
- **Manual verification**: Check CI logs show version output for each tool
