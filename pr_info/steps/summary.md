# Issue #256: Reduce Coordinator Duplicate Protection Threshold

## Overview

Reduce the coordinator's duplicate protection threshold from 60 seconds to 50 seconds to prevent legitimate Jenkins scheduled runs from being skipped due to timing variance.

## Problem Statement

The coordinator's duplicate protection skips execution if the last run was less than 60 seconds ago. Jenkins scheduler runs every minute with ±1-2 second timing variance. When Jenkins triggers at 59 seconds since the last check, the coordinator incorrectly skips the run:

```
2026-01-08 23:06:58,887 - mcp_coder.cli.commands.coordinator.core - INFO - Skipping mcp_coder - checked 59s ago
```

## Solution

Change the hardcoded 60-second threshold to 50 seconds, providing:
- ~10 second buffer for Jenkins timing variance
- Continued protection against accidental rapid double-runs (<50s)

## Architectural / Design Changes

**None.** This is a configuration value change, not an architectural modification.

- No new modules or classes
- No changes to control flow
- No changes to interfaces or APIs
- No changes to data structures

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/cli/commands/coordinator/core.py` | Modify | Change threshold constant from `60.0` to `50.0` |

## Files to Create

None.

## Test Impact

Existing tests use 30-second intervals which remain valid for both 60s and 50s thresholds. No test changes required.

## Implementation Steps

1. **Step 1**: Modify the duplicate protection threshold value (single line change)

## Risk Assessment

**Very Low Risk:**
- Single numeric constant change
- No logic changes
- No interface changes
- Existing tests continue to pass
