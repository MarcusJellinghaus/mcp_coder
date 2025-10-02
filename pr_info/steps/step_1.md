# Step 1: Create Package Structure

## Objective
Create the basic `llm/` package directory structure with empty `__init__.py` files. This establishes the foundation for all subsequent refactoring steps.

## Context
- **Reference**: See `pr_info/steps/summary.md` for complete architectural overview
- **Current State**: LLM code scattered across root level (`llm_types.py`, `llm_interface.py`, etc.)
- **Target State**: Consolidated under `src/mcp_coder/llm/` with clear sub-packages

## Files to Create

### Source Files (8 files)
```
src/mcp_coder/llm/__init__.py
src/mcp_coder/llm/formatting/__init__.py
src/mcp_coder/llm/storage/__init__.py
src/mcp_coder/llm/session/__init__.py
```

### Test Files (4 files)
```
tests/llm/__init__.py
tests/llm/formatting/__init__.py
tests/llm/storage/__init__.py
tests/llm/session/__init__.py
```

## Implementation

### WHERE
- `src/mcp_coder/llm/` - Main LLM package
- `src/mcp_coder/llm/formatting/` - Response formatting sub-package
- `src/mcp_coder/llm/storage/` - Session persistence sub-package
- `src/mcp_coder/llm/session/` - Session management sub-package
- `tests/llm/` - Test package mirroring source structure

### WHAT
Create empty package marker files with appropriate docstrings.

### HOW

**1. Create main package `__init__.py`:**
```python
# src/mcp_coder/llm/__init__.py
"""LLM functionality - provider interfaces, formatting, and session management.

This package consolidates all LLM-related functionality including:
- Provider interfaces (Claude, future providers)
- Response formatting (text, verbose, raw)
- Session management (storage, finding, resolution)
- Type definitions and serialization
"""

__all__: list[str] = []  # Will be populated in later steps
```

**2. Create sub-package `__init__.py` files:**
```python
# src/mcp_coder/llm/formatting/__init__.py
"""Response formatting and SDK object serialization utilities."""

__all__: list[str] = []

# src/mcp_coder/llm/storage/__init__.py
"""Session storage and retrieval functionality."""

__all__: list[str] = []

# src/mcp_coder/llm/session/__init__.py
"""Session management and resolution utilities."""

__all__: list[str] = []
```

**3. Create test package `__init__.py` files:**
```python
# tests/llm/__init__.py
"""Tests for LLM functionality."""

# tests/llm/formatting/__init__.py
"""Tests for response formatting."""

# tests/llm/storage/__init__.py
"""Tests for session storage."""

# tests/llm/session/__init__.py
"""Tests for session management."""
```

### ALGORITHM
```
1. Create directory: src/mcp_coder/llm/
2. Create directory: src/mcp_coder/llm/formatting/
3. Create directory: src/mcp_coder/llm/storage/
4. Create directory: src/mcp_coder/llm/session/
5. Create empty __init__.py in each directory with docstring
6. Repeat for tests/llm/ and subdirectories
```

### DATA
No data structures - only empty package files with docstrings.

## Testing

### Test Command
```bash
# Verify package structure exists
python -c "import mcp_coder.llm"
python -c "import mcp_coder.llm.formatting"
python -c "import mcp_coder.llm.storage"
python -c "import mcp_coder.llm.session"

# Run existing tests to ensure nothing broke
pytest tests/ -v
```

### Expected Result
- All directories created successfully
- All packages importable
- All existing tests still pass (no regressions)

## Verification Checklist
- [ ] Directory structure created
- [ ] All `__init__.py` files have proper docstrings
- [ ] Packages can be imported without errors
- [ ] Existing tests pass (no regressions)
- [ ] No functionality changed (structure only)

## LLM Prompt for Implementation

```
I'm implementing Step 1 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Create the basic package structure for the llm/ module with empty __init__.py files.

Please create:
1. Directory structure:
   - src/mcp_coder/llm/
   - src/mcp_coder/llm/formatting/
   - src/mcp_coder/llm/storage/
   - src/mcp_coder/llm/session/
   - tests/llm/
   - tests/llm/formatting/
   - tests/llm/storage/
   - tests/llm/session/

2. Empty __init__.py files with docstrings as specified in step_1.md

3. Verify all packages are importable

4. Run existing tests to ensure no regressions

This is a structure-only change - no functionality should change.
```

## Next Step
After this step completes successfully, proceed to **Step 2: Move Core Modules**.
