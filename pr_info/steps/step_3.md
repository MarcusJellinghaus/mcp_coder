# Step 3: Move and Update Tests

## Overview

Move existing tests from `tests/workflows/test_define_labels.py` to `tests/cli/commands/test_define_labels.py` and update imports.

## WHERE

- **Create**: `tests/cli/commands/test_define_labels.py`
- **Delete**: `tests/workflows/test_define_labels.py` (in Step 5)

## WHAT

### Test classes to move (update imports only):

1. `TestWorkflowLabelsFromConfig` - Tests loading labels from JSON config
2. `TestWorkflowLabelsContent` - Tests label metadata and coverage
3. `TestCalculateLabelChanges` - Unit tests for pure function
4. `TestApplyLabels` - Mocked integration tests for orchestrator
5. `TestArgumentParsing` - CLI argument parsing tests (REMOVE - handled by main.py now)
6. `TestResolveProjectDir` - Project directory validation tests

### New test class to add:

```python
class TestExecuteDefineLabels:
    """Test the CLI execute function."""
    
    def test_execute_define_labels_success(self, ...)
    def test_execute_define_labels_dry_run(self, ...)
    def test_execute_define_labels_invalid_project_dir(self, ...)
```

## HOW

### Import changes:

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
    resolve_project_dir,
)
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

## ALGORITHM

N/A - This step is moving/renaming only.

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
   - Update mock patches from `@patch("workflows.define_labels.LabelsManager")` to `@patch("mcp_coder.cli.commands.define_labels.LabelsManager")`

3. Remove `TestArgumentParsing` class (argument parsing is now handled by main.py's argparse)

4. Add a new `TestExecuteDefineLabels` class with tests:
   - `test_execute_define_labels_dry_run_success` - Test successful dry-run execution
   - Mock the dependencies appropriately

5. Keep all existing test logic - only change imports and mock paths

Reference: Look at `tests/cli/commands/test_verify.py` for patterns.

Do not delete the old test file yet - that happens in Step 5.
```

## Verification

- [ ] New test file created at correct location
- [ ] All imports updated to new module path
- [ ] All mock patches updated to new module path
- [ ] `TestArgumentParsing` class removed
- [ ] New `TestExecuteDefineLabels` class added
- [ ] All tests pass: `pytest tests/cli/commands/test_define_labels.py -v`
