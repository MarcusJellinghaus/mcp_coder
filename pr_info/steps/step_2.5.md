# Step 2.5: Add Validation and Robustness Enhancements

## Context
This step enhances the simplified implementation from Step 2 with validation and robustness features. We add empty string handling, path existence validation with fallback behavior, and clear logging to indicate which environment source was used.

**Reference:** See `pr_info/steps/summary.md` for full architectural context.

## WHERE: File Location
- **File**: `src/mcp_coder/llm/env.py`
- **Module**: `mcp_coder.llm.env`

## WHAT: Enhancements to Add

### Enhancement 1: Empty String Handling
Environment variables can be set to empty strings, which are truthy but invalid.

**Before (from Step 2):**
```python
runner_venv = os.environ.get("VIRTUAL_ENV")
if not runner_venv:
    runner_venv = os.environ.get("CONDA_PREFIX")
if not runner_venv:
    runner_venv = sys.prefix
```

**After (with empty string handling):**
```python
runner_venv = os.environ.get("VIRTUAL_ENV", "").strip()
if not runner_venv:
    runner_venv = os.environ.get("CONDA_PREFIX", "").strip()
if not runner_venv:
    runner_venv = sys.prefix
```

### Enhancement 2: Path Existence Validation with Fallback
If an environment variable points to a non-existent path, log a warning and fall back to the next option.

**Implementation:**
```python
def _get_runner_environment() -> tuple[str, str]:
    """Get runner environment path and source name.
    
    Returns:
        Tuple of (environment_path, source_name)
        
    Priority: VIRTUAL_ENV > CONDA_PREFIX > sys.prefix
    Invalid paths trigger fallback to next option with warning.
    """
    # Try VIRTUAL_ENV first
    virtual_env = os.environ.get("VIRTUAL_ENV", "").strip()
    if virtual_env and Path(virtual_env).exists():
        return virtual_env, "VIRTUAL_ENV"
    elif virtual_env:
        logger.warning(
            "VIRTUAL_ENV points to non-existent path: %s, trying next option",
            virtual_env
        )
    
    # Try CONDA_PREFIX second
    conda_prefix = os.environ.get("CONDA_PREFIX", "").strip()
    if conda_prefix and Path(conda_prefix).exists():
        return conda_prefix, "CONDA_PREFIX"
    elif conda_prefix:
        logger.warning(
            "CONDA_PREFIX points to non-existent path: %s, using sys.prefix",
            conda_prefix
        )
    
    # Fall back to sys.prefix (always valid)
    return sys.prefix, "sys.prefix"
```

### Enhancement 3: Source Logging
Add a single clear log statement showing which environment source was ultimately used.

**Implementation:**
```python
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    """Prepare MCP_CODER_* environment variables for LLM subprocess.
    
    [docstring content unchanged from Step 2]
    """
    logger.debug("Preparing LLM environment for project: %s", project_dir)

    # Get runner environment with validation and source tracking
    runner_venv, source = _get_runner_environment()
    
    logger.debug("Detected runner environment from %s: %s", source, runner_venv)

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

## HOW: Integration Points

### New Helper Function
- `_get_runner_environment() -> tuple[str, str]`: Private helper that encapsulates validation logic
- Returns both the path and the source name for logging
- Handles fallback chain: VIRTUAL_ENV → CONDA_PREFIX → sys.prefix

### Updated Main Function
- `prepare_llm_environment()` calls `_get_runner_environment()`
- Uses returned source name for clear logging
- Rest of function unchanged from Step 2

## ALGORITHM: Validation Logic

```
FOR each environment source in priority order:
    1. Get environment variable value
    2. Strip whitespace
    3. IF value is non-empty:
        a. Check if path exists
        b. IF exists:
            RETURN (path, source_name)
        c. ELSE:
            Log warning about invalid path
            Continue to next source
    4. IF value is empty:
        Continue to next source
END FOR

RETURN (sys.prefix, "sys.prefix")  # Always succeeds
```

## DATA: Return Values

### _get_runner_environment() Returns
```python
tuple[str, str]
```

### Examples
```python
# VIRTUAL_ENV set and valid
("/path/to/.venv", "VIRTUAL_ENV")

# VIRTUAL_ENV invalid, CONDA_PREFIX valid
("/home/user/conda/envs/myenv", "CONDA_PREFIX")

# Both invalid or unset
("/usr", "sys.prefix")
```

## Testing Updates

### Tests to Add

Add tests in `tests/llm/test_env.py` for validation behavior:

```python
def test_prepare_llm_environment_empty_virtual_env(tmp_path: Path) -> None:
    """Test that empty VIRTUAL_ENV falls back to CONDA_PREFIX."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    conda_env = tmp_path / "conda" / "envs" / "myenv"
    conda_env.mkdir(parents=True)
    
    # Set VIRTUAL_ENV to empty string
    env_vars = {
        "VIRTUAL_ENV": "   ",  # Whitespace only
        "CONDA_PREFIX": str(conda_env)
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        result = prepare_llm_environment(project_dir)
    
    assert result["MCP_CODER_VENV_DIR"] == str(conda_env.resolve())


def test_prepare_llm_environment_invalid_path_fallback(tmp_path: Path) -> None:
    """Test that non-existent VIRTUAL_ENV path falls back to CONDA_PREFIX."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    conda_env = tmp_path / "conda" / "envs" / "myenv"
    conda_env.mkdir(parents=True)
    
    # Set VIRTUAL_ENV to non-existent path
    env_vars = {
        "VIRTUAL_ENV": "/nonexistent/path/.venv",
        "CONDA_PREFIX": str(conda_env)
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        result = prepare_llm_environment(project_dir)
    
    assert result["MCP_CODER_VENV_DIR"] == str(conda_env.resolve())


def test_prepare_llm_environment_all_invalid_uses_sys_prefix(tmp_path: Path) -> None:
    """Test that all invalid paths fall back to sys.prefix."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Both VIRTUAL_ENV and CONDA_PREFIX invalid
    env_vars = {
        "VIRTUAL_ENV": "/nonexistent/venv",
        "CONDA_PREFIX": "/nonexistent/conda"
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch.object(sys, "prefix", "/usr"):
            result = prepare_llm_environment(project_dir)
    
    assert result["MCP_CODER_VENV_DIR"] == "/usr"
```

## Expected Result After This Step

**All validation works correctly:**
- ✅ Empty environment variables are skipped
- ✅ Invalid paths trigger warnings and fallback
- ✅ Logging shows which source was used
- ✅ All tests pass including new validation tests
- ✅ sys.prefix fallback always succeeds

## LLM Prompt for Implementation

```
Implement Step 2.5 from pr_info/steps/step_2.5.md with reference to pr_info/steps/summary.md.

Add validation and robustness to prepare_llm_environment():
1. Read the current implementation: src/mcp_coder/llm/env.py
2. Add the private helper function _get_runner_environment()
3. Update prepare_llm_environment() to use the helper
4. Add the three new validation tests to tests/llm/test_env.py
5. Run pytest to verify all tests pass

Use MCP tools exclusively:
- mcp__filesystem__read_file to read files
- mcp__filesystem__edit_file to make changes
- mcp__code-checker__run_pytest_check to verify tests pass

Focus on robustness: empty string handling, path validation, and clear logging.
```
