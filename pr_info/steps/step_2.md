# Step 2: Simplify Runner Environment Detection (TDD Green Phase)

## Context
This step implements the **Test-Driven Development GREEN phase**. We simplify `prepare_llm_environment()` to use direct environment queries instead of complex detection logic. This will make the tests from Step 1 pass.

**Note:** This step focuses on the core simplification. Validation enhancements (empty string handling, path existence checks, and logging) will be added in Step 2.5.

**Reference:** See `pr_info/steps/summary.md` for full architectural context.

## WHERE: File Location
- **File**: `src/mcp_coder/llm/env.py`
- **Module**: `mcp_coder.llm.env`

## WHAT: Functions to Modify

### Function Signature (Unchanged)
```python
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare environment variables for LLM subprocess execution.
    
    Args:
        project_dir: Directory containing code being developed
        
    Returns:
        Environment variables:
        - MCP_CODER_PROJECT_DIR: Where code lives (project_dir)
        - MCP_CODER_VENV_DIR: Where mcp-coder tools live (current process env)
    """
```

**Note:** Signature stays the same - this is backward compatible!

## HOW: Integration Points

### Imports to Keep
```python
import logging
import os
import sys
from pathlib import Path
```

### Imports to Remove
```python
from ..utils.detection import detect_python_environment  # ❌ Remove - no longer used
```

### Updated Import Block
```python
"""Environment variable preparation for LLM subprocess execution.

This module provides utilities for preparing environment variables that
enable portable .mcp.json configuration files across different machines.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
```

## ALGORITHM: Core Logic (Simple!)

Replace complex logic with direct environment query:

```
1. Check VIRTUAL_ENV environment variable (venv/virtualenv)
2. If not set, check CONDA_PREFIX (conda environments)
3. If not set, use sys.prefix (system Python, always available)
4. Resolve paths to absolute OS-native strings
5. Return dict with MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
```

## Detailed Implementation

### Before (Complex - 50+ lines)
```python
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    logger.debug("Preparing LLM environment for project: %s", project_dir)

    # Detect Python environment and virtual environment
    python_exe, venv_path = detect_python_environment(project_dir)  # ❌ Complex

    # Handle venv requirement based on platform
    if venv_path is None:
        if sys.platform.startswith("linux"):
            logger.debug("No venv found on Linux, using system Python at: %s", sys.prefix)
            venv_path = sys.prefix
        else:
            raise RuntimeError(
                f"No virtual environment found in {project_dir} and not running "
                "from a virtual environment.\n"
                "MCP Coder requires a venv to set MCP_CODER_VENV_DIR.\n"
                "Create one with: python -m venv .venv"
            )  # ❌ Unnecessary complexity

    # Convert paths to absolute OS-native strings
    project_dir_absolute = str(Path(project_dir).resolve())
    venv_dir_absolute = str(Path(venv_path).resolve())

    env_vars = {
        "MCP_CODER_PROJECT_DIR": project_dir_absolute,
        "MCP_CODER_VENV_DIR": venv_dir_absolute,
    }

    logger.debug(
        "Prepared environment variables: MCP_CODER_PROJECT_DIR=%s, MCP_CODER_VENV_DIR=%s",
        project_dir_absolute,
        venv_dir_absolute,
    )

    return env_vars
```

### After (Simple - 20 lines)
```python
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare MCP_CODER_* environment variables for LLM subprocess.

    This function prepares environment variables that can be used in .mcp.json
    configuration files to make them portable across different machines.
    
    The runner environment (MCP_CODER_VENV_DIR) is where mcp-coder is currently
    executing, detected from VIRTUAL_ENV, CONDA_PREFIX, or sys.prefix.

    Args:
        project_dir: Absolute path to project directory

    Returns:
        Dictionary with MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
        environment variables as absolute OS-native paths.
    """
    logger.debug("Preparing LLM environment for project: %s", project_dir)

    # Get runner environment (where mcp-coder is currently executing)
    # Priority: VIRTUAL_ENV > CONDA_PREFIX > sys.prefix
    runner_venv = os.environ.get("VIRTUAL_ENV")
    if not runner_venv:
        runner_venv = os.environ.get("CONDA_PREFIX")
    if not runner_venv:
        runner_venv = sys.prefix
    
    logger.debug("Detected runner environment: %s", runner_venv)

    # Convert paths to absolute OS-native strings
    project_dir_absolute = str(Path(project_dir).resolve())
    venv_dir_absolute = str(Path(runner_venv).resolve())

    env_vars = {
        "MCP_CODER_PROJECT_DIR": project_dir_absolute,
        "MCP_CODER_VENV_DIR": venv_dir_absolute,
    }

    logger.debug(
        "Prepared environment variables: MCP_CODER_PROJECT_DIR=%s, MCP_CODER_VENV_DIR=%s",
        project_dir_absolute,
        venv_dir_absolute,
    )

    return env_vars
```

## DATA: Return Values (Unchanged)

### Return Type
```python
dict[str, str]
```

### Return Structure
```python
{
    "MCP_CODER_PROJECT_DIR": "<absolute-path-to-project>",  # From parameter
    "MCP_CODER_VENV_DIR": "<absolute-path-to-runner-env>"   # From environment
}
```

### Example Return Values

#### Scenario 1: Virtual Environment
```python
# Environment: VIRTUAL_ENV = "C:\\projects\\runner\\.venv"
# Parameter: project_dir = "C:\\projects\\mycode"
{
    "MCP_CODER_PROJECT_DIR": "C:\\projects\\mycode",
    "MCP_CODER_VENV_DIR": "C:\\projects\\runner\\.venv"
}
```

#### Scenario 2: Conda Environment
```python
# Environment: CONDA_PREFIX = "/home/user/miniconda3/envs/myenv"
# Parameter: project_dir = "/workspace/project"
{
    "MCP_CODER_PROJECT_DIR": "/workspace/project",
    "MCP_CODER_VENV_DIR": "/home/user/miniconda3/envs/myenv"
}
```

#### Scenario 3: System Python
```python
# Environment: sys.prefix = "/usr"
# Parameter: project_dir = "/home/user/project"
{
    "MCP_CODER_PROJECT_DIR": "/home/user/project",
    "MCP_CODER_VENV_DIR": "/usr"
}
```

## Key Changes Summary

### Removed
- ❌ Call to `detect_python_environment(project_dir)`
- ❌ Platform-specific venv requirement checks
- ❌ RuntimeError for missing venv in project directory
- ❌ Complex fallback logic
- ❌ `python_exe` variable (unused)

### Added
- ✅ Direct query of `VIRTUAL_ENV` environment variable
- ✅ Fallback to `CONDA_PREFIX` environment variable
- ✅ Final fallback to `sys.prefix`
- ✅ Clearer debug logging for runner environment
- ✅ Updated docstring explaining runner environment detection

### Preserved
- ✅ Function signature (backward compatible)
- ✅ Return type and structure
- ✅ Path resolution to absolute OS-native strings
- ✅ Logging statements
- ✅ Variable names (`env_vars`, `project_dir_absolute`, `venv_dir_absolute`)

## Why This Works

1. **VIRTUAL_ENV**: Automatically set by venv/virtualenv when activated
2. **CONDA_PREFIX**: Automatically set by conda when environment is active
3. **sys.prefix**: Always points to the Python installation being used

**Key insight:** When mcp-coder runs, it's already executing in the runner environment. These variables tell us where we are!

## Backward Compatibility

### Co-located Runner and Project (Old Usage)
```python
# Before: Runner and project in same directory
# mcp-coder running from: /project/.venv/bin/mcp-coder
# VIRTUAL_ENV = "/project/.venv"
# project_dir = "/project"

# Result (same as before):
{
    "MCP_CODER_PROJECT_DIR": "/project",
    "MCP_CODER_VENV_DIR": "/project/.venv"  # Still works!
}
```

### Separate Runner and Project (New Use Case)
```python
# After: Runner and project separate (FIXED!)
# mcp-coder running from: /opt/mcp-coder/.venv/bin/mcp-coder
# VIRTUAL_ENV = "/opt/mcp-coder/.venv"
# project_dir = "/workspace/mycode"

# Result (now correct):
{
    "MCP_CODER_PROJECT_DIR": "/workspace/mycode",
    "MCP_CODER_VENV_DIR": "/opt/mcp-coder/.venv"  # Fixed!
}
```

## Expected Result After This Step

**All tests from Step 1 will PASS** (GREEN phase of TDD):
- Tests expect environment variables → implementation uses environment variables ✅
- Separate runner/project test passes ✅
- VIRTUAL_ENV, CONDA_PREFIX, sys.prefix tests all pass ✅

## LLM Prompt for Implementation

```
Implement Step 2 from pr_info/steps/step_2.md with reference to pr_info/steps/summary.md.

Follow Test-Driven Development GREEN phase:
1. Read the current implementation: src/mcp_coder/llm/env.py
2. Replace prepare_llm_environment() with the simplified version from this step
3. Remove the import for detect_python_environment (no longer used)
4. Keep all other imports (os, sys, logging, Path)
5. Update docstring to explain runner environment detection
6. Run pytest to verify tests PASS (green phase)

Use MCP tools exclusively:
- mcp__filesystem__read_file to read src/mcp_coder/llm/env.py
- mcp__filesystem__edit_file to make changes
- mcp__code-checker__run_pytest_check to verify tests pass

The tests from Step 1 should now all pass!
```
