# Step 4: Update Integration and Legacy Test Imports

## Context
Read `pr_info/steps/summary.md` for full architectural context.

This step updates the remaining test files that weren't updated in Step 2 - specifically the integration tests and legacy compatibility shim.

## Objective
Update import statements in integration and legacy test files to use the new module structure.

---

## WHERE - Files to Update

1. **`tests/workflows/test_create_pr_integration.py`** - Integration tests
2. **`tests/test_create_pr.py`** - Legacy backwards compatibility shim

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

### File 2: Legacy Compatibility Shim

**File:** `tests/test_create_pr.py`

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
FOR EACH file in [test_create_pr_integration.py, test_create_pr.py]:
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

# Test 2: Run legacy compatibility tests
pytest tests/test_create_pr.py -v
# Expected: All tests PASS

# Test 3: Run ALL create_pr related tests
pytest tests/ -k "create_pr" -v
# Expected: All tests PASS

# Test 4: Run full test suite to ensure nothing broke
pytest tests/workflows/create_pr/ -v
pytest tests/cli/commands/test_create_pr.py -v
# Expected: All tests PASS
```

### Code Quality Checks

```bash
# Pylint check on updated test files
pylint tests/workflows/test_create_pr_integration.py
pylint tests/test_create_pr.py

# Mypy check on updated test files
mypy tests/workflows/test_create_pr_integration.py
mypy tests/test_create_pr.py
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

**After:**
```python
from mcp_coder.workflows.create_pr.core import run_create_pr_workflow

@patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
def test_backwards_compatibility(mock_prereqs):
    # ...
```

**Note:** If `tests/test_create_pr.py` references `main()` function, it needs to be updated to reference `run_create_pr_workflow()` instead.

---

## SPECIAL CASE: main() Function References

If any test file calls or references the old `main()` function, it needs updating:

**Before:**
```python
from workflows.create_PR import main

def test_main():
    with pytest.raises(SystemExit):
        main()
```

**After:**
```python
from mcp_coder.workflows.create_pr.core import run_create_pr_workflow

def test_workflow():
    # Note: run_create_pr_workflow returns int, doesn't call sys.exit
    result = run_create_pr_workflow(project_dir, "claude", "cli")
    assert result == 0
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
   
2. Update tests/test_create_pr.py:
   - Change all "from workflows.create_PR" → "from mcp_coder.workflows.create_pr.core"
   - Change all "@patch("workflows.create_PR" → "@patch("mcp_coder.workflows.create_pr.core"
   - If it references main(), update to run_create_pr_workflow()
   
3. Run tests to verify:
   - pytest tests/workflows/test_create_pr_integration.py -v
   - pytest tests/test_create_pr.py -v
   - pytest tests/ -k "create_pr" -v
   
4. Run code quality checks on updated files

This is a simple find-and-replace task. No logic changes needed.
```

---

## Verification Checklist

- [ ] `tests/workflows/test_create_pr_integration.py` imports updated
- [ ] `tests/test_create_pr.py` imports updated
- [ ] All patch decorators updated
- [ ] Any `main()` references updated to `run_create_pr_workflow()`
- [ ] Integration tests pass
- [ ] Legacy tests pass
- [ ] All create_pr tests pass: `pytest tests/ -k "create_pr" -v`
- [ ] Pylint passes on updated test files
- [ ] Mypy passes on updated test files

---

## Dependencies

### Required Before This Step
- ✅ Step 2 completed (Workflow package exists with core.py)
- ✅ Step 2 already updated the main test files in `tests/workflows/create_pr/`

### Blocks
- Step 5 (legacy files can be removed once tests pass)

---

## Notes

- **Simple task:** This is primarily find-and-replace work
- **Low risk:** Tests will immediately show if imports are incorrect
- **Completes test migration:** After this step, ALL tests use new module structure
- **Enables cleanup:** Once tests pass, we can safely delete legacy files in Step 5
- Step 2 already updated the main test suite, this handles the outliers
