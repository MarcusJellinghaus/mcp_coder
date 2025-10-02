# Step 2: Move Core Modules

## Objective
Move existing stable modules (`llm_types.py`, `llm_interface.py`, `llm_serialization.py`) into the new `llm/` package and update all imports throughout the codebase.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 1 created the package structure
- **Current State**: Core modules at root level, all tests passing
- **Target State**: Core modules under `llm/`, all imports updated, tests passing

## Files to Move

```
src/mcp_coder/llm_types.py          → src/mcp_coder/llm/types.py
src/mcp_coder/llm_interface.py      → src/mcp_coder/llm/interface.py
src/mcp_coder/llm_serialization.py  → src/mcp_coder/llm/serialization.py
```

## Files to Modify

### Source Files (~10 files)
- `src/mcp_coder/__init__.py` - Update public API imports
- `src/mcp_coder/cli/commands/prompt.py` - Update LLM imports
- `src/mcp_coder/cli/commands/commit.py` - Update LLM imports (if applicable)
- `src/mcp_coder/prompt_manager.py` - Update imports (if applicable)
- `src/mcp_coder/llm_providers/claude/*.py` - Update imports in provider files

### Test Files (~10 files)
- `tests/test_llm_interface.py` - Update imports
- `tests/test_llm_serialization.py` - Update imports
- `tests/test_llm_types.py` - Update imports
- `tests/test_module_exports.py` - Update import tests
- `tests/test_module_integration.py` - Update integration tests
- `tests/cli/commands/test_prompt.py` - Update LLM imports
- `tests/llm_providers/claude/*.py` - Update imports in provider tests

## Implementation

### WHERE
1. Move files to: `src/mcp_coder/llm/`
2. Update imports in all files that reference these modules

### WHAT

**Main Functions (no signature changes):**
- All existing functions remain unchanged
- Only import paths change

**Key Import Updates:**
```python
# OLD imports
from mcp_coder.llm_types import LLMResponseDict, LLM_RESPONSE_VERSION
from mcp_coder.llm_interface import ask_llm, prompt_llm
from mcp_coder.llm_serialization import serialize_llm_response

# NEW imports
from mcp_coder.llm.types import LLMResponseDict, LLM_RESPONSE_VERSION
from mcp_coder.llm.interface import ask_llm, prompt_llm
from mcp_coder.llm.serialization import serialize_llm_response

# OR use clean public API
from mcp_coder.llm import ask_llm, prompt_llm, LLMResponseDict
```

### HOW

**Step 2.1: Move Files**
```bash
# Move files (preserve git history with git mv if using git)
git mv src/mcp_coder/llm_types.py src/mcp_coder/llm/types.py
git mv src/mcp_coder/llm_interface.py src/mcp_coder/llm/interface.py
git mv src/mcp_coder/llm_serialization.py src/mcp_coder/llm/serialization.py
```

**Step 2.2: Update `llm/__init__.py` Public API**
```python
"""LLM functionality - provider interfaces, formatting, and session management."""

from .interface import ask_llm, prompt_llm
from .serialization import (
    deserialize_llm_response,
    serialize_llm_response,
    to_json_string,
    from_json_string,
)
from .types import LLMResponseDict, LLM_RESPONSE_VERSION

__all__ = [
    # Public interfaces
    "ask_llm",
    "prompt_llm",
    # Serialization
    "serialize_llm_response",
    "deserialize_llm_response",
    "to_json_string",
    "from_json_string",
    # Types
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]
```

**Step 2.3: Update Root `__init__.py`**
```python
# Update imports from old paths to new paths
from .llm.interface import (
    ask_llm,
    deserialize_llm_response,
    prompt_llm,
    serialize_llm_response,
)
from .llm.types import LLM_RESPONSE_VERSION, LLMResponseDict
# ... rest of imports unchanged
```

**Step 2.4: Update All Import Statements**

Use find/replace in IDE or script:
```bash
# Find and replace pattern
OLD: from mcp_coder.llm_types import
NEW: from mcp_coder.llm.types import

OLD: from mcp_coder.llm_interface import
NEW: from mcp_coder.llm.interface import

OLD: from mcp_coder.llm_serialization import
NEW: from mcp_coder.llm.serialization import

# In llm/interface.py, update internal imports
OLD: from .llm_types import
NEW: from .types import

OLD: from .llm_serialization import
NEW: from .serialization import
```

### ALGORITHM
```
1. Move llm_types.py → llm/types.py (git mv)
2. Move llm_interface.py → llm/interface.py (git mv)
3. Move llm_serialization.py → llm/serialization.py (git mv)
4. Update llm/__init__.py with public API exports
5. Update root __init__.py imports
6. Find and replace import paths in all source files
7. Find and replace import paths in all test files
8. Run tests after each file update
```

### DATA

**Import Path Mapping:**
```python
{
    "llm_types": "llm.types",
    "llm_interface": "llm.interface",
    "llm_serialization": "llm.serialization",
}
```

## Testing

### Test Strategy (TDD)

**Test 2.1: Verify Module Imports**
```python
# tests/llm/test_module_structure.py (NEW)
def test_llm_package_structure():
    """Verify llm package structure and imports."""
    import mcp_coder.llm
    import mcp_coder.llm.types
    import mcp_coder.llm.interface
    import mcp_coder.llm.serialization
    
    # Verify public API available
    assert hasattr(mcp_coder.llm, 'ask_llm')
    assert hasattr(mcp_coder.llm, 'prompt_llm')
    assert hasattr(mcp_coder.llm, 'LLMResponseDict')

def test_public_api_exports():
    """Verify public API exports work."""
    from mcp_coder.llm import (
        ask_llm, 
        prompt_llm,
        LLMResponseDict,
        serialize_llm_response,
    )
    
    assert callable(ask_llm)
    assert callable(prompt_llm)
    assert callable(serialize_llm_response)
```

**Test 2.2: Run Existing Tests**
```bash
# All existing tests should pass with new import paths
pytest tests/test_llm_types.py -v
pytest tests/test_llm_interface.py -v
pytest tests/test_llm_serialization.py -v
pytest tests/cli/commands/test_prompt.py -v
pytest tests/llm_providers/ -v
pytest tests/ -v  # Full test suite
```

### Expected Results
- All imports resolve correctly
- No import errors in any module
- All existing tests pass unchanged
- Public API exports work from `mcp_coder.llm`

## Verification Checklist
- [ ] Files moved successfully (git history preserved if using git mv)
- [ ] `llm/__init__.py` exports public API
- [ ] Root `__init__.py` imports updated
- [ ] All source file imports updated
- [ ] All test file imports updated
- [ ] Module import test passes
- [ ] All existing tests pass
- [ ] No import errors when running code
- [ ] Public API accessible via `from mcp_coder.llm import ...`

## LLM Prompt for Implementation

```
I'm implementing Step 2 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Move core modules (llm_types.py, llm_interface.py, llm_serialization.py) into the llm/ package and update all imports.

Please:
1. Move the three files to llm/ directory:
   - llm_types.py → llm/types.py
   - llm_interface.py → llm/interface.py
   - llm_serialization.py → llm/serialization.py

2. Update llm/__init__.py to export the public API (see step_2.md)

3. Update src/mcp_coder/__init__.py imports

4. Find and replace all import statements throughout the codebase:
   - from mcp_coder.llm_types → from mcp_coder.llm.types
   - from mcp_coder.llm_interface → from mcp_coder.llm.interface
   - from mcp_coder.llm_serialization → from mcp_coder.llm.serialization

5. Update internal imports within llm/ modules

6. Create tests/llm/test_module_structure.py to verify imports

7. Run all existing tests to verify no regressions

This is an import path change only - no functionality changes.
```

## Next Step
After this step completes successfully, proceed to **Step 3: Move Providers Package**.
