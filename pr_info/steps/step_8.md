# Step 8: Code Review Follow-up Fixes

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.  
**Decisions:** See `pr_info/steps/decisions.md` (Decision 8) for all code review decisions.  
**Prerequisites:** Steps 0-7 must be complete.

## Objective
Address code review findings with three focused improvements:
1. Add stack trace logging for better debugging
2. Create pytest fixture to reduce test duplication
3. Fix cross-platform path consistency in .mcp.json

## WHERE

**Files to Modify:**
1. `src/mcp_coder/cli/commands/coordinator.py` - Add `exc_info=True` to exception logging
2. `tests/cli/commands/conftest.py` - Create pytest fixture for mock labels config (NEW FILE)
3. `.mcp.json` - Fix path separator for cross-platform support

**No New Functionality:**
- These are quality improvements, not feature changes
- All existing tests should continue to pass

## WHAT

### Part A: Improve Error Logging with Stack Traces

**Current Code (Line ~593):**
```python
except Exception as e:
    logger.error(f"Failed processing issue #{issue['number']}: {e}")
    print(f"Error: Failed to process issue #{issue['number']}: {e}", file=sys.stderr)
    return 1
```

**New Code:**
```python
except Exception as e:
    logger.error(f"Failed processing issue #{issue['number']}: {e}", exc_info=True)
    print(f"Error: Failed to process issue #{issue['number']}: {e}", file=sys.stderr)
    return 1
```

**Rationale:** Preserves full stack traces for debugging production issues without changing error messages.

### Part B: Create Pytest Fixture for Mock Labels Config

**New File: `tests/cli/commands/conftest.py`**
```python
"""Shared test fixtures for CLI commands tests."""
import pytest
from typing import Any, Dict


@pytest.fixture
def mock_labels_config() -> Dict[str, Any]:
    """Fixture providing standard mock labels configuration.
    
    This fixture reduces duplication across coordinator tests by providing
    a consistent mock label configuration structure.
    
    Returns:
        Dict with 'workflow_labels' and 'ignore_labels' keys matching
        the structure from config/labels.json
    """
    return {
        "workflow_labels": [
            {"name": "status-02:awaiting-planning", "category": "bot_pickup", "internal_id": "awaiting_planning"},
            {"name": "status-03:planning", "category": "bot_busy", "internal_id": "planning"},
            {"name": "status-05:plan-ready", "category": "bot_pickup", "internal_id": "plan_ready"},
            {"name": "status-06:implementing", "category": "bot_busy", "internal_id": "implementing"},
            {"name": "status-08:ready-pr", "category": "bot_pickup", "internal_id": "ready_pr"},
            {"name": "status-09:pr-creating", "category": "bot_busy", "internal_id": "pr_creating"},
        ],
        "ignore_labels": ["Overview"],
    }
```

**Usage Example (refactor existing tests):**
```python
# Before (in test method):
mock_load_labels.return_value = {
    "workflow_labels": [
        {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
        # ... repeated setup
    ],
    "ignore_labels": ["Overview"]
}

# After (in test method):
mock_load_labels.return_value = mock_labels_config
```

### Part C: Fix Cross-Platform Path Separator

**Current Code (`.mcp.json` line 25):**
```json
"command": "${MCP_CODER_VENV_DIR}\\Scripts\\mcp-server-filesystem.exe",
```

**New Code:**
```json
"command": "${MCP_CODER_VENV_DIR}/Scripts/mcp-server-filesystem.exe",
```

**Rationale:** Forward slashes work on all platforms (Windows, Linux, macOS). Matches the PYTHONPATH fix already implemented.

## HOW

### Integration Points

**Part A - Error Logging:**
- Location: `src/mcp_coder/cli/commands/coordinator.py`
- Function: `execute_coordinator_run()`
- Change: Add `exc_info=True` parameter to `logger.error()` calls in exception handlers
- Impact: Logs will include full stack traces for debugging

**Part B - Pytest Fixture:**
- Location: New file `tests/cli/commands/conftest.py`
- Impact: Tests can use `mock_labels_config` fixture instead of inline mock setup
- Refactor: Update existing test methods to use fixture (optional but recommended)

**Part C - Path Separator:**
- Location: `.mcp.json`
- Change: Replace backslash with forward slash in command path
- Impact: Consistent cross-platform path handling throughout config file

## ALGORITHM

No complex algorithms - these are simple fixes:

**Part A:**
```
1. Find exception handlers in execute_coordinator_run()
2. Add exc_info=True to logger.error() calls
3. Verify no change to error message format
```

**Part B:**
```
1. Create conftest.py in tests/cli/commands/
2. Define mock_labels_config fixture
3. Return standard label configuration dict
4. (Optional) Refactor existing tests to use fixture
```

**Part C:**
```
1. Open .mcp.json
2. Find line with \\Scripts\\
3. Replace with /Scripts/
4. Save file
```

## DATA

### Part A - No Data Structure Changes
- Stack traces added to logs only
- Error messages remain unchanged
- Return codes remain unchanged

### Part B - Fixture Return Value
```python
{
    "workflow_labels": [
        {
            "name": "status-02:awaiting-planning",
            "category": "bot_pickup",
            "internal_id": "awaiting_planning"
        },
        # ... (6 workflow labels total)
    ],
    "ignore_labels": ["Overview"]
}
```

### Part C - No Data Structure Changes
- String replacement only
- No functional changes to how paths are resolved

## Implementation Notes

1. **Part A - Find All Exception Handlers:**
   - Search for `logger.error(` in `execute_coordinator_run()`
   - Add `exc_info=True` to exception handling blocks
   - Do NOT change logger.info() or logger.debug() calls

2. **Part B - Fixture Scope:**
   - Use function scope (default) - each test gets fresh copy
   - No need for session or module scope
   - Fixture is read-only data, so no isolation concerns

3. **Part C - Verify Path Change:**
   - Test on both Windows and Linux if possible
   - Ensure MCP server still starts correctly
   - Forward slashes should work on all platforms

## LLM Prompt for Implementation

```
Implement Step 8 - Code Review Follow-up Fixes as described in pr_info/steps/summary.md.

See pr_info/steps/decisions.md (Decision 8) for the code review decisions.

Task: Apply three quality improvements from code review

Requirements:
1. Part A - Improve error logging:
   - Find exception handlers in execute_coordinator_run()
   - Add exc_info=True parameter to logger.error() calls
   - Keep error messages unchanged
   - Only modify exception handling blocks

2. Part B - Create pytest fixture:
   - Create new file: tests/cli/commands/conftest.py
   - Define mock_labels_config fixture returning standard label config
   - Include all 6 workflow labels (status-02, 03, 05, 06, 08, 09)
   - Include ignore_labels: ["Overview"]
   - Add docstring explaining fixture purpose

3. Part C - Fix path separator:
   - Open .mcp.json
   - Line 25: Change ${MCP_CODER_VENV_DIR}\\Scripts\\ to ${MCP_CODER_VENV_DIR}/Scripts/
   - Ensure forward slash consistency

4. Verify changes:
   - Run existing tests - all should still pass
   - No functional changes, only quality improvements
   - No new tests needed (testing existing functionality)

Follow the exact specifications in step_8.md.
Apply KISS principle - minimal changes, maximum benefit.
```

## Test Execution

**Run existing tests to verify no breakage:**
```python
# Run all coordinator tests
pytest tests/cli/commands/test_coordinator.py -v

# Run all CLI tests
pytest tests/cli/test_main.py -v

# Run fast unit tests
pytest -m "not git_integration and not claude_integration and not formatter_integration and not github_integration" -v
```

**Expected:** All tests pass unchanged (no new tests needed for these fixes).

## Success Criteria

- ✅ Part A: Exception handlers include `exc_info=True` for stack traces
- ✅ Part B: `tests/cli/commands/conftest.py` created with `mock_labels_config` fixture
- ✅ Part C: `.mcp.json` uses forward slashes for all paths
- ✅ All existing tests still pass
- ✅ No functional changes - only quality improvements
- ✅ Documentation improvements only, no new features

## Notes

**Optional Enhancements (not required for this step):**
- Refactor existing test methods to use the new fixture
- Add more fixtures for other commonly mocked objects
- These can be done as future cleanup tasks

**Testing:**
- No new tests required - these are quality improvements
- Existing tests validate that nothing broke
- Manual testing on both Windows and Linux recommended for .mcp.json change
