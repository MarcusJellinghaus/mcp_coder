# Issue #151: Fix MCP Environment Configuration for Separate Runner/Project Directories

## Problem Statement

**Current Issue:** `prepare_llm_environment()` incorrectly assumes the runner environment (where mcp-coder is installed) and project directory (code being developed) are co-located. When they are separate, MCP tools execute using the wrong Python environment, causing test failures and tool errors.

**Real-world Failure Scenario:**
- **Runner**: `C:\AutoRunner\local-windows\mcp_coder_prod\.venv` (has current mcp-coder tools)
- **Project**: `C:\AutoRunner\local-windows\targets\mcp_coder\.venv` (outdated development environment)
- **Result**: MCP tools run with outdated project environment instead of current runner environment

## Root Cause

In `src/mcp_coder/llm/env.py`:
```python
def prepare_llm_environment(project_dir: Path) -> dict[str, str]:
    # ❌ WRONG: Searches for venv INSIDE project_dir
    python_exe, venv_path = detect_python_environment(project_dir)
```

This searches for a virtual environment **inside the project directory**, but MCP tools need the environment **where mcp-coder is currently running**.

## Architectural/Design Changes

### KISS Principle Solution

**Before (Complex):**
- Search project directory for virtual environment
- Complex detection logic with platform-specific handling
- Assumes runner and project are co-located

**After (Simple):**
- Use environment variables that Python automatically sets
- Direct query: `VIRTUAL_ENV` or `sys.prefix`
- Clean separation: runner environment (where we execute) vs project directory (what we analyze)

### Key Insight

**The runner environment is where THIS process is executing.** Python automatically tells us this via:
1. `VIRTUAL_ENV` environment variable (if in venv/virtualenv)
2. `CONDA_PREFIX` environment variable (if in conda)
3. `sys.prefix` (always set, works for any Python installation)

No detection needed - just read the environment!

### Environment Variable Semantics (Updated)

| Variable | Old Meaning | New Meaning |
|----------|-------------|-------------|
| `MCP_CODER_PROJECT_DIR` | Project code location | ✅ Unchanged: Project code location |
| `MCP_CODER_VENV_DIR` | ❌ Venv found in project | ✅ Runner environment (where mcp-coder executes) |

### Universal Compatibility

Works with all installation types:
- ✅ Virtual environment (venv, virtualenv)
- ✅ Conda environment
- ✅ System Python
- ✅ Container installations
- ✅ CI/CD environments

## Files to Create or Modify

### Modified Files

1. **`src/mcp_coder/llm/env.py`** (MODIFIED)
   - Simplify `prepare_llm_environment()` function
   - Remove call to `detect_python_environment(project_dir)`
   - Use `os.environ.get("VIRTUAL_ENV")` or `os.environ.get("CONDA_PREFIX")` or `sys.prefix`
   - Remove unused imports and platform-specific logic

2. **`tests/llm/test_env.py`** (MODIFIED)
   - Update existing tests for new behavior
   - Add test: runner with `VIRTUAL_ENV` set
   - Add test: runner with `CONDA_PREFIX` set
   - Add test: runner with system Python (`sys.prefix`)
   - Add test: separate runner/project directories
   - Remove tests for unused `detect_python_environment()` logic

### No New Files

This is a simplification - we're removing complexity, not adding it.

## Implementation Approach

### Test-Driven Development

**Step 1:** Update tests first (test_env.py)
- Define expected behavior with new environment detection
- Tests will fail initially (red phase)

**Step 2:** Simplify implementation (env.py)
- Replace complex logic with direct environment queries
- Tests pass (green phase)

**Step 3:** Run full quality checks
- Pytest (all tests pass)
- Pylint (code quality)
- Mypy (type checking)

### Minimal Changes Principle

- ✅ Only modify `env.py` and `test_env.py`
- ✅ No new functions or modules
- ✅ No workflow changes
- ✅ Backward compatible (co-located runner/project still works)

## Benefits

1. **Simpler Code**: ~90% less complexity in environment detection
2. **More Reliable**: Uses Python's built-in environment information
3. **Universal**: Works across all Python installation types
4. **Maintainable**: Less code = fewer bugs
5. **Backward Compatible**: Existing usage patterns continue to work

## Acceptance Criteria

- [ ] `prepare_llm_environment()` uses `VIRTUAL_ENV`, `CONDA_PREFIX`, or `sys.prefix`
- [ ] `MCP_CODER_VENV_DIR` points to runner environment (current process)
- [ ] `MCP_CODER_PROJECT_DIR` points to project directory (parameter)
- [ ] Works when runner and project are separate directories
- [ ] Works when runner and project are co-located (backward compatible)
- [ ] All existing tests pass
- [ ] New tests cover venv, conda, and system Python scenarios
- [ ] Pylint, pytest, and mypy all pass

## Testing Strategy

### Unit Tests (Fast)
- Mock environment variables (`VIRTUAL_ENV`, `CONDA_PREFIX`)
- Mock `sys.prefix`
- Test all installation type scenarios
- No actual file system or process execution

### Integration Tests (Not Required)
- Actual separate runner/project setup would require complex test fixtures
- Unit tests with mocks are sufficient for this change

## Risk Assessment

**Low Risk Change:**
- ✅ Pure simplification (removing code)
- ✅ Well-tested behavior (Python's environment variables)
- ✅ Backward compatible
- ✅ No breaking API changes
- ✅ Isolated to one module (`env.py`)

## Related Documentation

- `.mcp.json` already correctly uses `${MCP_CODER_VENV_DIR}` - no changes needed
- MCP servers correctly interpret environment variables - no changes needed
