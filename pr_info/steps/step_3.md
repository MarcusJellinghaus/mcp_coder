# Step 3: Move and Update Tests

## Overview

Move existing tests from `tests/workflows/test_define_labels.py` to `tests/cli/commands/test_define_labels.py`, update imports, and fix tests that expect `SystemExit` to expect `ValueError`.

## WHERE

- **Create**: `tests/cli/commands/test_define_labels.py`
- **Delete**: `tests/workflows/test_define_labels.py` (in Step 5)

**Note**: `tests/workflows/implement/test_core.py` was already updated in Step 1 as part of the refactoring checkpoint.

## WHAT

### Test classes to move (with import updates):

1. `TestWorkflowLabelsFromConfig` - Tests loading labels from JSON config
2. `TestWorkflowLabelsContent` - Tests label metadata and coverage
3. `TestCalculateLabelChanges` - Unit tests for pure function
4. `TestApplyLabels` - Mocked integration tests for orchestrator (update for new exception pattern)
5. `TestResolveProjectDir` - Project directory validation tests (update `SystemExit` → `ValueError`)

### Test class to REMOVE:

- `TestArgumentParsing` - No longer needed; argument parsing is handled by `main.py`'s argparse

### New test class to add (MINIMAL):

```python
class TestExecuteDefineLabels:
    """Test the CLI execute function - minimal tests for wiring."""
    
    def test_execute_define_labels_dry_run_returns_zero(self, ...):
        """Test successful dry-run execution returns 0."""
        ...
    
    def test_execute_define_labels_invalid_dir_returns_one(self, ...):
        """Test invalid project dir returns 1."""
        ...
```

Only 1-2 tests needed - the core logic is already tested by `TestApplyLabels`.

## HOW

### Import changes in new test file:

**Old imports:**
```python
from workflows.define_labels import (
    apply_labels,
    calculate_label_changes,
    parse_arguments,
    resolve_project_dir,
)
```

**New imports:**
```python
from mcp_coder.cli.commands.define_labels import (
    apply_labels,
    calculate_label_changes,
    execute_define_labels,
)
from mcp_coder.workflows.utils import resolve_project_dir
```

### Mock path changes:

**Old:**
```python
@patch("workflows.define_labels.LabelsManager")
```

**New:**
```python
@patch("mcp_coder.cli.commands.define_labels.LabelsManager")
```

### Update `TestApplyLabels` for exception pattern:

The `apply_labels` function now raises `RuntimeError` instead of calling `sys.exit(1)`:

```python
# BEFORE: Test expected SystemExit
with pytest.raises(SystemExit) as exc_info:
    apply_labels(tmp_path, workflow_labels, dry_run=False)
assert exc_info.value.code == 1

# AFTER: Test expects RuntimeError
with pytest.raises(RuntimeError, match="Failed to create label"):
    apply_labels(tmp_path, workflow_labels, dry_run=False)
```

### Update `TestResolveProjectDir` for exception pattern:

```python
# BEFORE
with pytest.raises(SystemExit) as exc_info:
    resolve_project_dir(nonexistent_path)
assert exc_info.value.code == 1

# AFTER
with pytest.raises(ValueError, match="does not exist"):
    resolve_project_dir(nonexistent_path)
```

## ALGORITHM

N/A - This step is moving/renaming and updating exception expectations.

## DATA

No data structure changes - tests use same fixtures and mocks.

## LLM Prompt

```
Please implement Step 3 of the implementation plan in `pr_info/steps/step_3.md`.

Context: See `pr_info/steps/summary.md` for the overall plan.

Task: Move and update the tests:

1. Create `tests/cli/commands/test_define_labels.py` by copying from `tests/workflows/test_define_labels.py`

2. Update all imports:
   - Change `from workflows.define_labels import ...` to `from mcp_coder.cli.commands.define_labels import ...`
   - Import `resolve_project_dir` from `mcp_coder.workflows.utils`
   - Update mock patches from `@patch("workflows.define_labels.LabelsManager")` to `@patch("mcp_coder.cli.commands.define_labels.LabelsManager")`

3. Remove `TestArgumentParsing` class entirely (argument parsing is now handled by main.py)

4. Update `TestResolveProjectDir` tests:
   - Change `pytest.raises(SystemExit)` to `pytest.raises(ValueError)`
   - Remove assertions on `exc_info.value.code`
   - Add `match=` parameter to verify error messages

5. Update `TestApplyLabels` tests:
   - Change `pytest.raises(SystemExit)` to `pytest.raises(RuntimeError)` for API errors
   - Update error message match patterns

6. Add minimal `TestExecuteDefineLabels` class with only 1-2 tests:
   - `test_execute_define_labels_dry_run_returns_zero` - Mock dependencies, verify returns 0
   - `test_execute_define_labels_invalid_dir_returns_one` - Invalid path returns 1

Reference: Look at `tests/cli/commands/test_create_pr.py` for patterns.

Note: `tests/workflows/implement/test_core.py` was already updated in Step 1.

Do not delete the old test file yet - that happens in Step 5.
```

## Verification

- [ ] New test file created at `tests/cli/commands/test_define_labels.py`
- [ ] All imports updated to new module paths
- [ ] All mock patches updated to new module paths
- [ ] `TestArgumentParsing` class removed
- [ ] `TestResolveProjectDir` tests expect `ValueError` instead of `SystemExit`
- [ ] `TestApplyLabels` API error tests expect `RuntimeError` instead of `SystemExit`
- [ ] Minimal `TestExecuteDefineLabels` class added (1-2 tests)
- [ ] All tests pass: `pytest tests/cli/commands/test_define_labels.py -v`

### Code Quality Checks:
- [ ] `mcp__code-checker__run_pylint_check()` - No errors
- [ ] `mcp__code-checker__run_pytest_check()` - All tests pass
- [ ] `mcp__code-checker__run_mypy_check()` - No type errors
