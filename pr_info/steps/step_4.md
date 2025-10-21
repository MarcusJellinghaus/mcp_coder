# Step 4: Update Integration and Legacy Test Imports

## Context
Read `pr_info/steps/summary.md` for full architectural context.

This step updates the remaining test files that weren't updated in Step 2 - specifically the integration tests and legacy compatibility shim.

## Objective
Update import statements in integration and legacy test files to use the new module structure.

---

## WHERE - Files to Update

1. **`tests/workflows/test_create_pr_integration.py`** - Integration tests

**Note:** `tests/test_create_pr.py` (legacy compatibility shim) will be deleted in Step 5, not updated.

---

## WHAT - Import Updates

### File 1: Integration Tests

**File:** `tests/workflows/test_create_pr_integration.py`

**Find and replace:**
```python
# OLD
from workflows.create_PR import <function_name>

# NEW
from mcp_coder.workflows.create_pr.core import <function_name>
```

**Patch path updates:**
```python
# OLD
@patch("workflows.create_PR.<function_name>")

# NEW
@patch("mcp_coder.workflows.create_pr.core.<function_name>")
```



---

## HOW - Step-by-Step Process

### Step 1: Read Current Import Patterns

```bash
# View current imports in integration tests
cat tests/workflows/test_create_pr_integration.py | grep "from workflows.create_PR"
cat tests/workflows/test_create_pr_integration.py | grep "@patch(\"workflows.create_PR"

# View current imports in legacy tests
cat tests/test_create_pr.py | grep "from workflows.create_PR"
cat tests/test_create_pr.py | grep "@patch(\"workflows.create_PR"
```

### Step 2: Update Integration Tests

Open `tests/workflows/test_create_pr_integration.py` and update all occurrences:

**Import statements:**
- `from workflows.create_PR import` → `from mcp_coder.workflows.create_pr.core import`

**Patch decorators:**
- `@patch("workflows.create_PR.` → `@patch("mcp_coder.workflows.create_pr.core.`

### Step 3: Update Legacy Tests

Open `tests/test_create_pr.py` and update all occurrences:

**Import statements:**
- `from workflows.create_PR import` → `from mcp_coder.workflows.create_pr.core import`

**Patch decorators:**
- `@patch("workflows.create_PR.` → `@patch("mcp_coder.workflows.create_pr.core.`

---

## ALGORITHM - Update Process (Pseudocode)

```
FOR file test_create_pr_integration.py:
    1. Read file contents
    2. Replace "from workflows.create_PR" → "from mcp_coder.workflows.create_pr.core"
    3. Replace "@patch(\"workflows.create_PR" → "@patch(\"mcp_coder.workflows.create_pr.core"
    4. Replace "workflows.create_PR" in any other context → "mcp_coder.workflows.create_pr.core"
    5. Save file
    6. Run tests to verify
```

---

## VALIDATION

### Test Execution

```bash
# Test 1: Run integration tests
pytest tests/workflows/test_create_pr_integration.py -v
# Expected: All tests PASS

# Test 2: Run ALL create_pr related tests
pytest tests/ -k "create_pr" -v
# Expected: All tests PASS

# Test 3: Run full test suite to ensure nothing broke
pytest tests/workflows/create_pr/ -v
pytest tests/cli/commands/test_create_pr.py -v
# Expected: All tests PASS
```

### Code Quality Checks

```bash
# Pylint check on updated test file
pylint tests/workflows/test_create_pr_integration.py

# Mypy check on updated test file
mypy tests/workflows/test_create_pr_integration.py
```

---

## DATA - Expected Changes

### Integration Tests File

**Before:**
```python
from workflows.create_PR import (
    check_prerequisites,
    generate_pr_summary,
    # ... other imports
)

@patch("workflows.create_PR.is_working_directory_clean")
@patch("workflows.create_PR.get_incomplete_tasks")
def test_something(mock_tasks, mock_clean):
    # ...
```

**After:**
```python
from mcp_coder.workflows.create_pr.core import (
    check_prerequisites,
    generate_pr_summary,
    # ... other imports
)

@patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
@patch("mcp_coder.workflows.create_pr.core.get_incomplete_tasks")
def test_something(mock_tasks, mock_clean):
    # ...
```

### Legacy Tests File

**Before:**
```python
from workflows.create_PR import main

@patch("workflows.create_PR.check_prerequisites")
def test_backwards_compatibility(mock_prereqs):
    # ...
```



---

## LLM Prompt for This Step

```
I'm implementing Step 4 of the create_PR to CLI command conversion (Issue #139).

Context: Read pr_info/steps/summary.md for full architectural context.

Task: Update remaining test file imports (integration and legacy tests).

Step 4 Details: Read pr_info/steps/step_4.md

Instructions:
1. Update tests/workflows/test_create_pr_integration.py:
   - Change all "from workflows.create_PR" → "from mcp_coder.workflows.create_pr.core"
   - Change all "@patch("workflows.create_PR" → "@patch("mcp_coder.workflows.create_pr.core"
   
2. Run tests to verify:
   - pytest tests/workflows/test_create_pr_integration.py -v
   - pytest tests/ -k "create_pr" -v
   
3. Run code quality checks on updated file

Note: tests/test_create_pr.py will be deleted in Step 5, not updated here.

This is a simple find-and-replace task. No logic changes needed.
```

---

## Verification Checklist

- [ ] `tests/workflows/test_create_pr_integration.py` imports updated
- [ ] All patch decorators updated
- [ ] Integration tests pass
- [ ] All create_pr tests pass: `pytest tests/ -k "create_pr" -v`
- [ ] Pylint passes on updated test file
- [ ] Mypy passes on updated test file

---

## Dependencies

### Required Before This Step
- ✅ Step 2 completed (Workflow package exists with core.py)
- ✅ Step 2 already updated the main test files in `tests/workflows/create_pr/`

### Blocks
- Step 5 (legacy files can be removed once tests pass)

---

## Notes

- **Simple task:** This is primarily find-and-replace work for one file
- **Low risk:** Tests will immediately show if imports are incorrect
- **Legacy shim handling:** `tests/test_create_pr.py` is just a re-export shim and will be deleted in Step 5
- Step 2 already updated the main test suite, this handles the integration tests
