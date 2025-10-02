# Step 8: Move Core Tests

## Objective
Move existing test files to mirror the new `llm/` module structure. This establishes the foundation for test organization that matches code organization.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 7 moved session logic, all tests passing
- **Current State**: Test files at root level don't mirror new structure
- **Target State**: Test structure mirrors code structure under `tests/llm/`

## Files to Move

```
tests/test_llm_types.py          → tests/llm/test_types.py
tests/test_llm_interface.py      → tests/llm/test_interface.py
tests/test_llm_serialization.py  → tests/llm/test_serialization.py
tests/llm_providers/             → tests/llm/providers/
```

## Files to Modify

```
tests/llm/test_types.py          (Update imports after move)
tests/llm/test_interface.py      (Update imports after move)
tests/llm/test_serialization.py  (Update imports after move)
tests/llm/providers/claude/*.py  (Update imports after move)
tests/test_module_exports.py     (Update import test paths if needed)
```

## Implementation

### WHERE
- Move from: `tests/` root level
- Move to: `tests/llm/` matching source structure
- Update: Import statements in moved files

### WHAT

**Files to Move (4 items):**
1. `test_llm_types.py` → `llm/test_types.py`
2. `test_llm_interface.py` → `llm/test_interface.py`
3. `test_llm_serialization.py` → `llm/test_serialization.py`
4. `llm_providers/` directory → `llm/providers/` directory

**Import Updates Needed:**
```python
# In tests/llm/test_types.py
# OLD
from mcp_coder.llm_types import LLMResponseDict, LLM_RESPONSE_VERSION

# NEW
from mcp_coder.llm.types import LLMResponseDict, LLM_RESPONSE_VERSION

# Similar updates for test_interface.py and test_serialization.py
```

### HOW

**Step 8.1: Move Test Files**

```bash
# Move test files (preserve git history)
git mv tests/test_llm_types.py tests/llm/test_types.py
git mv tests/test_llm_interface.py tests/llm/test_interface.py
git mv tests/test_llm_serialization.py tests/llm/test_serialization.py
git mv tests/llm_providers tests/llm/providers
```

**Step 8.2: Update Imports in `test_types.py`**

```python
# In tests/llm/test_types.py
# Update all imports from old paths to new paths
from mcp_coder.llm.types import LLMResponseDict, LLM_RESPONSE_VERSION
```

**Step 8.3: Update Imports in `test_interface.py`**

```python
# In tests/llm/test_interface.py
from mcp_coder.llm.interface import ask_llm, prompt_llm
from mcp_coder.llm.types import LLMResponseDict
# ... other imports updated
```

**Step 8.4: Update Imports in `test_serialization.py`**

```python
# In tests/llm/test_serialization.py
from mcp_coder.llm.serialization import (
    to_json_string,
    from_json_string,
    serialize_llm_response,
    deserialize_llm_response,
)
from mcp_coder.llm.types import LLMResponseDict
```

**Step 8.5: Update Imports in Provider Tests**

```python
# In tests/llm/providers/claude/*.py
# Update any imports that reference old paths
from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.llm.providers.claude.claude_code_api import ask_claude_code_api
# etc.
```

### ALGORITHM
```
1. Move test_llm_types.py → llm/test_types.py
2. Move test_llm_interface.py → llm/test_interface.py
3. Move test_llm_serialization.py → llm/test_serialization.py
4. Move llm_providers/ → llm/providers/
5. Update imports in test_types.py
6. Update imports in test_interface.py
7. Update imports in test_serialization.py
8. Update imports in provider tests
9. Run each test file after update
10. Run full test suite
```

### DATA

**File Mapping:**
```python
{
    "tests/test_llm_types.py": "tests/llm/test_types.py",
    "tests/test_llm_interface.py": "tests/llm/test_interface.py",
    "tests/test_llm_serialization.py": "tests/llm/test_serialization.py",
    "tests/llm_providers/": "tests/llm/providers/",
}
```

**Import Updates:**
```python
{
    "mcp_coder.llm_types": "mcp_coder.llm.types",
    "mcp_coder.llm_interface": "mcp_coder.llm.interface",
    "mcp_coder.llm_serialization": "mcp_coder.llm.serialization",
    "mcp_coder.llm_providers": "mcp_coder.llm.providers",
}
```

## Testing

### Test Strategy (TDD)

**Test 8.1: Verify Moved Tests Run**

```bash
# Run each moved test file individually
pytest tests/llm/test_types.py -v
pytest tests/llm/test_interface.py -v
pytest tests/llm/test_serialization.py -v
pytest tests/llm/providers/claude/ -v
```

**Test 8.2: Verify Test Discovery**

```bash
# Verify pytest discovers all tests in new location
pytest tests/llm/ --collect-only
# Should show all tests from moved files
```

**Test 8.3: Run Full Test Suite**

```bash
# Ensure nothing broke
pytest tests/ -v
```

**Test 8.4: Verify Old Test Files Gone**

```bash
# Should not exist anymore
ls tests/test_llm_types.py 2>&1 | grep "No such file"
ls tests/test_llm_interface.py 2>&1 | grep "No such file"
ls tests/test_llm_serialization.py 2>&1 | grep "No such file"
ls tests/llm_providers/ 2>&1 | grep "No such file"
```

### Expected Results
- All moved test files run successfully
- Test discovery works in new location
- No test failures
- Old test files deleted
- Test structure now mirrors code structure

## Verification Checklist
- [ ] `test_llm_types.py` moved to `llm/test_types.py`
- [ ] `test_llm_interface.py` moved to `llm/test_interface.py`
- [ ] `test_llm_serialization.py` moved to `llm/test_serialization.py`
- [ ] `llm_providers/` moved to `llm/providers/`
- [ ] All imports updated in moved files
- [ ] Each moved test file runs successfully
- [ ] Test discovery works
- [ ] Old test files deleted
- [ ] Full test suite passes
- [ ] Test structure mirrors code structure
- [ ] Create `tests/llm/conftest.py` only if shared fixtures are needed

## LLM Prompt for Implementation

```
I'm implementing Step 8 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Move core test files to mirror the new llm/ module structure.

Please:
1. Move test files:
   - tests/test_llm_types.py → tests/llm/test_types.py
   - tests/test_llm_interface.py → tests/llm/test_interface.py
   - tests/test_llm_serialization.py → tests/llm/test_serialization.py
   - tests/llm_providers/ → tests/llm/providers/

2. Update imports in all moved test files:
   - from mcp_coder.llm_types → from mcp_coder.llm.types
   - from mcp_coder.llm_interface → from mcp_coder.llm.interface
   - from mcp_coder.llm_serialization → from mcp_coder.llm.serialization
   - from mcp_coder.llm_providers → from mcp_coder.llm.providers

3. Run tests after each move:
   - pytest tests/llm/test_types.py -v
   - pytest tests/llm/test_interface.py -v
   - pytest tests/llm/test_serialization.py -v
   - pytest tests/llm/providers/ -v

4. Verify test discovery: pytest tests/llm/ --collect-only

5. Run full test suite: pytest tests/ -v

This reorganizes tests to mirror code structure - no test logic changes.
```

## Next Step
After this step completes successfully, proceed to **Step 9: Extract Formatting Tests**.
