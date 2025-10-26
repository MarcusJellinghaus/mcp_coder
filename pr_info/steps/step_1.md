# Step 1: Update Tests for Runner Environment Detection (TDD Red Phase)

## Context
This step implements the **Test-Driven Development RED phase**. We update tests to define the new expected behavior: `prepare_llm_environment()` should use the runner's environment (where mcp-coder executes) instead of searching in the project directory.

**Reference:** See `pr_info/steps/summary.md` for full architectural context.

## WHERE: File Location
- **File**: `tests/llm/test_env.py`
- **Module**: `tests.llm.test_env`

## WHAT: Test Functions to Add/Modify

### 1. Add New Test: Runner with VIRTUAL_ENV
```python
def test_prepare_llm_environment_uses_virtual_env_variable(tmp_path: Path) -> None:
    """Test that VIRTUAL_ENV is used for runner environment."""
```

### 2. Add New Test: Runner with CONDA_PREFIX
```python
def test_prepare_llm_environment_uses_conda_prefix(tmp_path: Path) -> None:
    """Test that CONDA_PREFIX is used when VIRTUAL_ENV not set."""
```

### 3. Add New Test: Runner with System Python
```python
def test_prepare_llm_environment_uses_sys_prefix_fallback(tmp_path: Path) -> None:
    """Test that sys.prefix is used when no venv/conda variables set."""
```

### 4. Add New Test: Separate Runner and Project Directories
```python
def test_prepare_llm_environment_separate_runner_project(tmp_path: Path) -> None:
    """Test runner env and project dir are independent."""
```

### 5. Update Existing Test: Remove detect_python_environment Mock
```python
def test_prepare_llm_environment_success(tmp_path: Path) -> None:
    # Remove mock for detect_python_environment (no longer used)
    # Add mock for VIRTUAL_ENV instead
```

## HOW: Integration Points

### Imports Required
```python
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
```

### Mocking Strategy
- Mock `os.environ` to set `VIRTUAL_ENV` or `CONDA_PREFIX`
- Mock `sys.prefix` for system Python scenarios
- No longer mock `detect_python_environment()` (removed in Step 2)

## ALGORITHM: Test Logic Pattern

For each new test:
```
1. Create temporary runner environment directory
2. Create temporary project directory (separate location)
3. Mock environment variable (VIRTUAL_ENV, CONDA_PREFIX, or sys.prefix)
4. Call prepare_llm_environment(project_dir)
5. Assert MCP_CODER_VENV_DIR == runner environment (mocked)
6. Assert MCP_CODER_PROJECT_DIR == project directory (parameter)
```

## DATA: Expected Test Results

### Test 1: VIRTUAL_ENV Priority
```python
# Input:
VIRTUAL_ENV = "/path/to/runner/.venv"
project_dir = "/path/to/project"

# Expected Output:
{
    "MCP_CODER_PROJECT_DIR": "/path/to/project",
    "MCP_CODER_VENV_DIR": "/path/to/runner/.venv"  # From VIRTUAL_ENV
}
```

### Test 2: CONDA_PREFIX Fallback
```python
# Input:
VIRTUAL_ENV = None  # Not set
CONDA_PREFIX = "/home/user/miniconda3/envs/myenv"
project_dir = "/path/to/project"

# Expected Output:
{
    "MCP_CODER_PROJECT_DIR": "/path/to/project",
    "MCP_CODER_VENV_DIR": "/home/user/miniconda3/envs/myenv"  # From CONDA_PREFIX
}
```

### Test 3: sys.prefix Fallback
```python
# Input:
VIRTUAL_ENV = None  # Not set
CONDA_PREFIX = None  # Not set
sys.prefix = "/usr" or "C:\\Python311"
project_dir = "/path/to/project"

# Expected Output:
{
    "MCP_CODER_PROJECT_DIR": "/path/to/project",
    "MCP_CODER_VENV_DIR": "/usr"  # From sys.prefix
}
```

### Test 4: Separate Directories
```python
# Input:
VIRTUAL_ENV = "/opt/mcp-coder/.venv"  # Runner location
project_dir = "/workspace/myproject"  # Different location

# Expected Output:
{
    "MCP_CODER_PROJECT_DIR": "/workspace/myproject",  # From parameter
    "MCP_CODER_VENV_DIR": "/opt/mcp-coder/.venv"      # From VIRTUAL_ENV
}
# Proves runner and project are independent!
```

## Detailed Test Implementation

### Test 1: VIRTUAL_ENV Variable
```python
def test_prepare_llm_environment_uses_virtual_env_variable(tmp_path: Path) -> None:
    """Test that VIRTUAL_ENV environment variable is used for runner environment."""
    # Arrange
    runner_venv = tmp_path / "runner" / ".venv"
    runner_venv.mkdir(parents=True)
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Act
    with patch.dict(os.environ, {"VIRTUAL_ENV": str(runner_venv)}):
        result = prepare_llm_environment(project_dir)
    
    # Assert
    assert result["MCP_CODER_VENV_DIR"] == str(runner_venv.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())
```

### Test 2: CONDA_PREFIX Fallback
```python
def test_prepare_llm_environment_uses_conda_prefix(tmp_path: Path) -> None:
    """Test that CONDA_PREFIX is used when VIRTUAL_ENV not set."""
    # Arrange
    conda_env = tmp_path / "miniconda3" / "envs" / "myenv"
    conda_env.mkdir(parents=True)
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Act - Clear VIRTUAL_ENV, set CONDA_PREFIX
    env_vars = os.environ.copy()
    env_vars.pop("VIRTUAL_ENV", None)  # Ensure not set
    env_vars["CONDA_PREFIX"] = str(conda_env)
    
    with patch.dict(os.environ, env_vars, clear=True):
        result = prepare_llm_environment(project_dir)
    
    # Assert
    assert result["MCP_CODER_VENV_DIR"] == str(conda_env.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())
```

### Test 3: sys.prefix Fallback
```python
def test_prepare_llm_environment_uses_sys_prefix_fallback(tmp_path: Path) -> None:
    """Test that sys.prefix is used when no venv/conda variables set."""
    # Arrange
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    system_prefix = "/usr" if sys.platform != "win32" else "C:\\Python311"
    
    # Act - Clear both VIRTUAL_ENV and CONDA_PREFIX
    env_vars = os.environ.copy()
    env_vars.pop("VIRTUAL_ENV", None)
    env_vars.pop("CONDA_PREFIX", None)
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch.object(sys, "prefix", system_prefix):
            result = prepare_llm_environment(project_dir)
    
    # Assert
    assert result["MCP_CODER_VENV_DIR"] == str(Path(system_prefix).resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())
```

### Test 4: Separate Runner and Project
```python
def test_prepare_llm_environment_separate_runner_project(tmp_path: Path) -> None:
    """Test that runner environment and project directory are independent."""
    # Arrange - Create separate locations
    runner_location = tmp_path / "opt" / "mcp-coder" / ".venv"
    runner_location.mkdir(parents=True)
    
    project_location = tmp_path / "workspace" / "myproject"
    project_location.mkdir(parents=True)
    
    # Act
    with patch.dict(os.environ, {"VIRTUAL_ENV": str(runner_location)}):
        result = prepare_llm_environment(project_location)
    
    # Assert - They should be completely different paths
    assert result["MCP_CODER_VENV_DIR"] == str(runner_location.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_location.resolve())
    
    # Verify they're truly separate
    venv_path = Path(result["MCP_CODER_VENV_DIR"])
    project_path = Path(result["MCP_CODER_PROJECT_DIR"])
    assert not venv_path.is_relative_to(project_path)
    assert not project_path.is_relative_to(venv_path)
```

### Test 5: Update Existing Success Test
```python
def test_prepare_llm_environment_success(tmp_path: Path) -> None:
    """Test successful environment preparation with valid venv."""
    # Arrange
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = tmp_path / "runner" / ".venv"
    venv_dir.mkdir(parents=True)

    # Act - Use VIRTUAL_ENV instead of mocking detect_python_environment
    with patch.dict(os.environ, {"VIRTUAL_ENV": str(venv_dir)}):
        result = prepare_llm_environment(project_dir)

    # Assert
    assert "MCP_CODER_PROJECT_DIR" in result
    assert "MCP_CODER_VENV_DIR" in result
    assert Path(result["MCP_CODER_PROJECT_DIR"]).is_absolute()
    assert Path(result["MCP_CODER_VENV_DIR"]).is_absolute()
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())
    assert result["MCP_CODER_VENV_DIR"] == str(venv_dir.resolve())
```

## Tests to Remove/Update

### Remove: test_prepare_llm_environment_no_venv
This test checked for `RuntimeError` when no venv found in project. We no longer search the project directory, so this test is obsolete. The new behavior always succeeds (uses `sys.prefix` as fallback).

**Action:** Delete this test or replace with new fallback test (Test 3 above).

## Expected Result After This Step

**All new tests will FAIL** (RED phase of TDD):
- `prepare_llm_environment()` still uses old logic (`detect_python_environment`)
- Tests expect new logic (environment variables)
- This is correct and expected!

Next step (Step 2) will update the implementation to make tests pass (GREEN phase).

## LLM Prompt for Implementation

```
Implement Step 1 from pr_info/steps/step_1.md with reference to pr_info/steps/summary.md.

Follow Test-Driven Development:
1. Read the current test file: tests/llm/test_env.py
2. Add the four new test functions as specified in this step
3. Update the existing test_prepare_llm_environment_success test
4. Remove or replace test_prepare_llm_environment_no_venv
5. Run pytest to verify tests FAIL (expected in RED phase)

Use MCP tools exclusively:
- mcp__filesystem__read_file to read tests/llm/test_env.py
- mcp__filesystem__edit_file to make changes
- mcp__code-checker__run_pytest_check to run tests (expect failures)

Do NOT modify src/mcp_coder/llm/env.py in this step - that comes in Step 2.
```
