# Issue #192: Update Coordinator Command Templates for Windows

## Overview

Update the coordinator command templates in `coordinator.py` to match the actual Jenkins scripts used in production. The current templates are missing several important elements.

## Architectural / Design Changes

**None** - This is a content-only update to existing string templates. No new functions, classes, or architectural changes are required.

## Changes Required

### 1. Add `--update-labels` Flag
All workflow commands (create-plan, implement, create-pr) should include `--update-labels` to automatically update GitHub issue labels on successful completion.

### 2. Add `DISABLE_AUTOUPDATER=1` Environment Variable
Prevents Claude CLI from checking for updates during automated execution. Required for all templates.

### 3. Standardize MCP Config Path
Linux templates currently use `.mcp.linux.json` - should be standardized to `.mcp.json` for both Windows and Linux.

### 4. Add MCP Verification Steps (Test Templates Only)
Test templates should include comprehensive MCP server connectivity verification.

### 5. Add Archive Directory Listing
All templates should include diagnostic output at the end showing archive directories.

## Files to Modify

| File | Change Type |
|------|-------------|
| `src/mcp_coder/cli/commands/coordinator.py` | Modify 8 template strings |
| `tests/cli/commands/test_coordinator.py` | Update test assertions |

## Template Changes Summary

| Template | `DISABLE_AUTOUPDATER` | `--update-labels` | `.mcp.json` | MCP Verification | Archive Listing |
|----------|----------------------|-------------------|-------------|------------------|-----------------|
| `DEFAULT_TEST_COMMAND_WINDOWS` | Add | N/A | Already correct | Add | Add |
| `CREATE_PLAN_COMMAND_WINDOWS` | Add | Add | Already correct | N/A | Add |
| `IMPLEMENT_COMMAND_WINDOWS` | Add | Add | Already correct | N/A | Add |
| `CREATE_PR_COMMAND_WINDOWS` | Add | Add | Already correct | N/A | Add |
| `DEFAULT_TEST_COMMAND` | Add | N/A | Already correct | Add | Add |
| `CREATE_PLAN_COMMAND_TEMPLATE` | Add | Add | Fix | N/A | Add |
| `IMPLEMENT_COMMAND_TEMPLATE` | Add | Add | Fix | N/A | Add |
| `CREATE_PR_COMMAND_TEMPLATE` | Add | Add | Fix | N/A | Add |

## Implementation Steps

- **Step 1**: Update Windows templates and their tests
- **Step 2**: Update Linux templates and their tests
