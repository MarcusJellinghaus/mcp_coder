# Step 2: Update Template to Use --extra dev

## LLM Prompt
```
Reference pr_info/steps/summary.md for context.

Implement Step 2: Update VENV_SECTION_WINDOWS template to use '--extra dev' instead of 
'--extra types' to install complete development dependencies including test tools.

The test from Step 1 should now pass after this change.
```

## Objective
Modify the VENV_SECTION_WINDOWS template to install all dev dependencies, fixing the issue where test dependencies were missing.

## WHERE

### Source File
**Path**: `src/mcp_coder/workflows/vscodeclaude/templates.py`

**Location in File**: Line ~14 in VENV_SECTION_WINDOWS constant
```python
VENV_SECTION_WINDOWS = r"""echo Checking Python environment...
if not exist .venv\Scripts\activate.bat (
    echo Creating virtual environment...
    uv venv
    ...
    echo Installing dependencies...
    uv sync --extra types    # <-- THIS LINE
    ...
)
```

## WHAT

### Change Required
**Before**:
```batch
uv sync --extra types
```

**After**:
```batch
uv sync --extra dev
```

### Why This Change
From `pyproject.toml`, the `dev` group includes:
- `types`: Type stubs (what was previously installed)
- `test`: pytest-asyncio, pytest-xdist (MISSING - fixes the issue)
- `mcp`: MCP servers
- Architecture tools: import-linter, pycycle, tach, vulture

## HOW

### Edit Strategy
Use the Edit tool to replace the specific line:

```python
Edit(
    file_path="src/mcp_coder/workflows/vscodeclaude/templates.py",
    old_string="    uv sync --extra types",
    new_string="    uv sync --extra dev"
)
```

### Context for Edit
The line appears within the VENV_SECTION_WINDOWS constant:
- After: `echo Installing dependencies...`
- Before: `if errorlevel 1 (`

## ALGORITHM

```
1. Read src/mcp_coder/workflows/vscodeclaude/templates.py
2. Locate VENV_SECTION_WINDOWS constant definition
3. Find line containing "uv sync --extra types"
4. Replace with "uv sync --extra dev"
5. Preserve all whitespace and indentation
```

## DATA

### Input
**Current Template** (excerpt):
```batch
VENV_SECTION_WINDOWS = r"""echo Checking Python environment...
if not exist .venv\Scripts\activate.bat (
    echo Creating virtual environment...
    uv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    uv sync --extra types
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    set VENV_CREATED=1
) else (
    set VENV_CREATED=0
)
```

### Output
**Updated Template** (excerpt):
```batch
VENV_SECTION_WINDOWS = r"""echo Checking Python environment...
if not exist .venv\Scripts\activate.bat (
    echo Creating virtual environment...
    uv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    uv sync --extra dev
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    set VENV_CREATED=1
) else (
    set VENV_CREATED=0
)
```

## Implementation Details

### Exact String to Replace
Find this exact string (with proper indentation):
```python
    uv sync --extra types
```

Replace with:
```python
    uv sync --extra dev
```

### No Other Changes
- ✅ Change only the dependency flag
- ❌ Don't modify error messages
- ❌ Don't modify echo statements
- ❌ Don't modify error handling logic
- ❌ Don't touch other templates (Linux not implemented yet)

## Verification

### Run the Test from Step 1
```bash
pytest tests/workflows/vscodeclaude/test_templates.py::test_venv_section_installs_dev_dependencies -v
```

### Expected Result (After Step 2)
```
PASSED - Test verifies VENV_SECTION_WINDOWS uses '--extra dev'
```

### Manual Verification
Read the updated file and confirm:
1. Line contains `uv sync --extra dev`
2. No occurrence of `uv sync --extra types` remains
3. All surrounding context is unchanged
4. Indentation is preserved

## Success Criteria
- ✅ Template uses `--extra dev` instead of `--extra types`
- ✅ Test from Step 1 passes
- ✅ No other template modifications
- ✅ Code quality checks pass (no syntax errors)

## Impact
After this change, all new vscodeclaude workspaces will:
- ✅ Have test dependencies (pytest-asyncio, pytest-xdist)
- ✅ Have type stubs (existing behavior preserved)
- ✅ Have complete development environment
- ✅ Be able to run `pytest` successfully

## Notes
- This is the core fix for issue #411
- Change is minimal and low-risk
- Existing workspaces are unaffected (only new workspace creation)
- Users can manually update existing workspaces with `uv sync --extra dev`
