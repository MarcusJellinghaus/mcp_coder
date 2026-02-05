# Step 1: Add Test for Dev Dependencies in Template

## LLM Prompt
```
Reference pr_info/steps/summary.md for context.

Implement Step 1: Add test to verify that VENV_SECTION_WINDOWS template contains '--extra dev' 
for installing complete development dependencies.

Follow TDD approach - write the test first (it will fail), then we'll fix the implementation in Step 2.
```

## Objective
Write a test that verifies the VENV_SECTION_WINDOWS template uses `--extra dev` instead of `--extra types`.

## WHERE

### Test File
**Path**: `tests/workflows/vscodeclaude/test_templates.py`

**Why**: 
- Tests for `src/mcp_coder/workflows/vscodeclaude/templates.py`
- Follows existing test structure pattern

## WHAT

### Test Function
```python
def test_venv_section_installs_dev_dependencies():
    """Test that VENV_SECTION_WINDOWS installs dev dependencies including test tools."""
    ...
```

**Purpose**: Verify template uses `--extra dev` to install all development dependencies

**Assertions**:
1. Template contains `uv sync --extra dev`
2. Template does NOT contain `uv sync --extra types` (old behavior)

## HOW

### Integration Points

**Imports**:
```python
from mcp_coder.workflows.vscodeclaude.templates import VENV_SECTION_WINDOWS
```

**Test Pattern**: Simple string assertion test
- No mocking required
- No fixtures needed
- Direct constant access

## ALGORITHM

```
1. Import VENV_SECTION_WINDOWS from templates module
2. Assert "uv sync --extra dev" is in template string
3. Assert "uv sync --extra types" is NOT in template string (prevents regression)
4. Add docstring explaining why dev dependencies are needed
```

## DATA

### Input
- `VENV_SECTION_WINDOWS`: String constant from templates module

### Expected Behavior
```python
# Template should contain this line:
"uv sync --extra dev"

# Template should NOT contain this line anymore:
"uv sync --extra types"
```

### Test Output
- **Before Step 2**: Test FAILS (template still has `--extra types`)
- **After Step 2**: Test PASSES (template uses `--extra dev`)

## Implementation Details

### Full Test Implementation
```python
def test_venv_section_installs_dev_dependencies():
    """Test that VENV_SECTION_WINDOWS installs dev dependencies.
    
    The dev dependencies include:
    - types: Type stubs for mypy
    - test: pytest-asyncio, pytest-xdist for running tests
    - mcp: MCP server dependencies
    - Architecture tools: import-linter, pycycle, tach, vulture
    
    This ensures vscodeclaude workspaces have complete development environments.
    """
    # Verify correct installation command
    assert "uv sync --extra dev" in VENV_SECTION_WINDOWS, (
        "VENV_SECTION_WINDOWS should install dev dependencies with '--extra dev'"
    )
    
    # Verify old behavior is removed (prevent regression)
    assert "uv sync --extra types" not in VENV_SECTION_WINDOWS, (
        "VENV_SECTION_WINDOWS should not use '--extra types' (incomplete dependencies)"
    )
```

### Test File Structure
If `test_templates.py` doesn't exist, create it with:
```python
"""Tests for vscodeclaude template strings."""

from mcp_coder.workflows.vscodeclaude.templates import VENV_SECTION_WINDOWS


def test_venv_section_installs_dev_dependencies():
    # ... test implementation ...
```

## Verification

### Run the Test
```bash
pytest tests/workflows/vscodeclaude/test_templates.py::test_venv_section_installs_dev_dependencies -v
```

### Expected Result (Before Step 2)
```
FAILED - AssertionError: VENV_SECTION_WINDOWS should install dev dependencies with '--extra dev'
```

### Success Criteria
- Test file created in correct location
- Test imports VENV_SECTION_WINDOWS successfully
- Test fails as expected (TDD red phase)
- Test has clear docstring explaining requirements

## Notes
- This test is intentionally simple - no complex setup required
- Direct string matching is appropriate for template validation
- Test will guide the implementation in Step 2
