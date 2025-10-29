# Step 7: Code Review Follow-up

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.  
**Decisions:** See `pr_info/steps/decisions.md` (Decision 7) for all code review decisions.  
**Prerequisites:** Steps 0-6 must be complete.

## Objective
Address code review findings by adding documentation, fixing cross-platform issues, and clarifying design decisions.

## WHERE

**Files to Modify:**
1. `.mcp.json` - Fix PYTHONPATH for cross-platform support
2. `src/mcp_coder/cli/commands/coordinator.py` - Add documentation comments
3. `src/mcp_coder/utils/github_operations/label_config.py` - Add module docstring

**No Test Files:**
- These are documentation and minor fixes, no new functionality

## WHAT

### Part A: Fix PYTHONPATH Configuration

**Current (Windows-only):**
```json
"PYTHONPATH": "${MCP_CODER_PROJECT_DIR}\\src;${MCP_CODER_PROJECT_DIR}"
```

**New (Cross-platform):**
```json
"PYTHONPATH": "${MCP_CODER_PROJECT_DIR}/src"
```

**Changes:**
1. Use forward slash (works on Windows and Linux)
2. Remove second path (no longer needed after refactoring)

### Part B: Add Documentation Comments to coordinator.py

**Location 1: Command Templates (before CREATE_PLAN_COMMAND_TEMPLATE)**
```python
# Command templates for Jenkins workflows
# IMPORTANT: These templates assume Jenkins workspace clones repository to /workspace/repo
# The --project-dir parameter must match the Jenkins workspace structure
# All templates follow the pattern:
#   1. Checkout appropriate branch (main for planning, feature branch for implementation/PR)
#   2. Pull latest code
#   3. Verify tool versions
#   4. Sync dependencies
#   5. Execute mcp-coder command
CREATE_PLAN_COMMAND_TEMPLATE = """git checkout main
...
```

**Location 2: WORKFLOW_MAPPING (before the constant)**
```python
# Workflow configuration mapping
# IMPORTANT: Label names must match those defined in config/labels.json
# Uses GitHub API label names directly (not internal_ids) for simpler code
WORKFLOW_MAPPING = {
    "status-02:awaiting-planning": {
...
```

### Part C: Add Module Docstring to label_config.py

**Add at top of file (after imports):**
```python
"""Label configuration loading utilities.

This module provides functions to load and parse GitHub label configurations
from JSON files. It supports both local project overrides and bundled package
configurations.

Typical usage pattern:
    # Load configuration for a project
    config_path = get_labels_config_path(project_dir)
    labels_config = load_labels_config(config_path)
    
    # Build lookup dictionaries if needed
    label_lookups = build_label_lookups(labels_config)
    
    # Access label information
    bot_pickup_labels = {
        name for name, category in label_lookups["name_to_category"].items()
        if category == "bot_pickup"
    }

The module tries local project configuration first (workflows/config/labels.json),
then falls back to the bundled package configuration if local doesn't exist.
"""
```

## HOW

### Integration Points

**No new integrations** - only documentation changes:
1. `.mcp.json` environment variable
2. Python docstrings and comments
3. No code logic changes

### Implementation Notes

1. **PYTHONPATH Change**: Forward slashes work cross-platform because Python's import system normalizes paths
2. **Comment Placement**: Comments immediately before the constants they document
3. **Module Docstring**: Follows Google/NumPy style with examples

## ALGORITHM

No algorithms - documentation only changes:
```
1. Update .mcp.json PYTHONPATH value
2. Add comment before CREATE_PLAN_COMMAND_TEMPLATE
3. Add comment before WORKFLOW_MAPPING
4. Add module docstring to label_config.py
5. Verify no code logic changes
```

## DATA

No data structures change - only documentation:
- `.mcp.json`: String value change (PYTHONPATH)
- Python files: Comment/docstring additions

## LLM Prompt for Implementation

```
Implement Step 7 - Code Review Follow-up as described in pr_info/steps/summary.md.

See pr_info/steps/decisions.md (Decision 7) for the code review decisions.

Task: Add documentation and fix cross-platform configuration

Requirements:
1. Fix .mcp.json:
   - Change PYTHONPATH to: "${MCP_CODER_PROJECT_DIR}/src"
   - Use forward slash for cross-platform compatibility
   - Remove second path (no longer needed)

2. Add comments to src/mcp_coder/cli/commands/coordinator.py:
   - Before CREATE_PLAN_COMMAND_TEMPLATE: Explain /workspace/repo requirement
   - Before WORKFLOW_MAPPING: Explain label names must match config

3. Add module docstring to src/mcp_coder/utils/github_operations/label_config.py:
   - Explain purpose and usage pattern
   - Include example code showing typical usage
   - Document fallback behavior (local → bundled)

4. Verify changes:
   - No code logic changes
   - Only documentation and configuration
   - No new tests needed

Follow the exact specifications in step_7.md.
Apply KISS principle - minimal changes, maximum clarity.
```

## Success Criteria

- ✅ `.mcp.json` uses cross-platform PYTHONPATH
- ✅ Command templates documented with Jenkins workspace requirement
- ✅ WORKFLOW_MAPPING documented with config dependency
- ✅ label_config.py has comprehensive module docstring
- ✅ No code logic changes
- ✅ Existing tests still pass
- ✅ Documentation is clear and helpful
