# Step 1: Create Environment Variable Preparation Module

## Context
Read `pr_info/steps/summary.md` for full context. This step creates the core module for preparing MCP Coder environment variables.

## WHERE

**New files:**
- `src/mcp_coder/llm/env.py`
- `tests/llm/test_env.py`

## WHAT

### Function Signature
```python
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare MCP_CODER_* environment variables for LLM subprocess.
    
    Args:
        project_dir: Absolute path to project directory
        
    Returns:
        Dictionary with MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
        
    Raises:
        RuntimeError: If virtual environment not found
    """
```

## HOW

**Imports:**
```python
import logging
from pathlib import Path
from ..utils.detection import detect_python_environment

logger = logging.getLogger(__name__)
```

**Integration:**
- Uses existing `detect_python_environment()` from `src/mcp_coder/utils/detection.py`
- Will be called by workflows (`run_implement_workflow`, `generate_commit_message_with_llm`)

## ALGORITHM

```
1. Log debug message: preparing environment for project_dir
2. Call detect_python_environment(project_dir)
3. If venv_path is None: raise RuntimeError with clear message
4. Convert project_dir to absolute string via Path.resolve()
5. Convert venv_path to absolute string via Path.resolve()
6. Log debug message with prepared environment variables
7. Return dict with both environment variables
```

## DATA

**Return value:**
```python
{
    'MCP_CODER_PROJECT_DIR': 'C:\\Users\\user\\project',  # OS-native format
    'MCP_CODER_VENV_DIR': 'C:\\Users\\user\\project\\.venv'
}
```

**Error cases:**
- Raises `RuntimeError(f"No virtual environment found in {project_dir} and not running from a virtual environment.\nMCP Coder requires a venv to set MCP_CODER_VENV_DIR.\nCreate one with: python -m venv .venv")`

## Test Coverage

**Test cases:**
1. `test_prepare_llm_environment_success()` - Valid venv found
2. `test_prepare_llm_environment_no_venv()` - No venv, raises RuntimeError
3. `test_prepare_llm_environment_paths_absolute()` - Verifies absolute paths
4. `test_prepare_llm_environment_paths_os_native()` - Verifies OS-native format

## LLM Prompt

```
I'm implementing environment variable support for MCP Coder to make .mcp.json portable.

Context: Read pr_info/steps/summary.md for full architectural overview.

Task: Implement Step 1 - Create environment variable preparation module.

Requirements:
1. Create src/mcp_coder/llm/env.py with prepare_llm_environment(project_dir: Path) function
2. Use existing detect_python_environment() from utils/detection.py
3. Return dict with MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR
4. Raise RuntimeError if venv not found (strict requirement)
5. Use OS-native path format via str(Path.resolve())

Test-Driven Development:
1. First create tests/llm/test_env.py with 4 test cases
2. Then implement src/mcp_coder/llm/env.py
3. Run tests to verify

Follow the specifications in pr_info/steps/step_1.md exactly.
```
