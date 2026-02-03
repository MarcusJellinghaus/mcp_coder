# Issue #402: Fix MCP Filesystem Server Directory Mismatch

## Problem Statement

The `.vscodeclaude_start.bat` template does not set `MCP_CODER_PROJECT_DIR` before calling `claude --resume`. When this environment variable is inherited from a parent shell with a different value, MCP filesystem operations silently affect the wrong codebase.

## Root Cause

| File | Sets MCP_CODER_PROJECT_DIR? |
|------|----------------------------|
| `claude.bat` (works) | Yes - `set "MCP_CODER_PROJECT_DIR=%CD%"` |
| `.vscodeclaude_start.bat` (broken) | No - inherits from shell |

## Solution Overview

### Architectural Changes

**None** - This is a template content fix, not an architectural change. The module structure, interfaces, and data flow remain unchanged.

### Design Changes

1. **Template Enhancement**: Add environment variable setup to `VENV_SECTION_WINDOWS` template
2. **Defense in Depth**: Add mismatch detection warning before setting variables
3. **Naming Cleanup**: Remove obsolete `_V2` suffix from template constants

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Modify | Add env var setup + warning to `VENV_SECTION_WINDOWS`; rename 4 constants |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Modify | Update 8 references to renamed constants |
| `tests/workflows/vscodeclaude/test_workspace.py` | Modify | Extend existing test to verify env vars |

## Implementation Steps

| Step | Description | TDD Approach |
|------|-------------|--------------|
| 1 | Add env var setup and warning to `VENV_SECTION_WINDOWS` | Extend test first, then fix template |
| 2 | Remove V2 suffix from 4 template names and update 8 usages | Verify tests still pass |
| 3 | Final verification | Run all tests |

## Acceptance Criteria

- [ ] `VENV_SECTION_WINDOWS` sets `MCP_CODER_PROJECT_DIR=%CD%`
- [ ] `VENV_SECTION_WINDOWS` sets `MCP_CODER_VENV_DIR=%CD%\.venv`
- [ ] Warning with pause displayed when `MCP_CODER_PROJECT_DIR` doesn't match CWD
- [ ] V2 suffix removed from 4 template names in `templates.py`
- [ ] 8 references updated in `workspace.py`
- [ ] Test extended to verify environment variable setup
- [ ] All tests pass
