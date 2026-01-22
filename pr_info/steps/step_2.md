# Step 2: Add Pytest Fixture and Refactor Test

## LLM Prompt

```
Implement Step 2 of Issue #91 (see pr_info/steps/summary.md).

In tests/formatters/test_integration.py:
1. Add required imports (contextlib, Generator from typing)
2. Create a pytest fixture `temp_integration_file` with yield pattern
3. Refactor `test_complete_tool_integration_workflow` to use the fixture
```

## WHERE

- **File**: `tests/formatters/test_integration.py`
- **Location**: 
  - Imports: Add to existing import block (lines 1-15)
  - Fixture: Add before `TestQualityGatesValidation` class (around line 300)
  - Test: Modify `test_complete_tool_integration_workflow` method (lines 340-372)

## WHAT

### New Imports

```python
import contextlib
from typing import Generator  # Add to existing typing imports
```

### New Fixture

```python
@pytest.fixture
def temp_integration_file() -> Generator[Path, None, None]:
    """Fixture for temp file in project root with pytest-managed cleanup."""
    ...
```

### Modified Test Signature

```python
def test_complete_tool_integration_workflow(self, temp_integration_file: Path) -> None:
```

## HOW

- Fixture decorated with `@pytest.fixture` (function-scoped by default)
- Test method accepts fixture as parameter (pytest dependency injection)
- Cleanup uses `contextlib.suppress(OSError)` for robustness

## ALGORITHM

### Fixture Logic (5 lines)

```
1. Calculate project_root from __file__ path
2. Create test_file path as project_root / "temp_integration_test.py"
3. yield test_file to the test
4. After test completes (success or failure):
5.   Suppress OSError and call test_file.unlink(missing_ok=True)
```

### Test Refactoring

```
1. Accept temp_integration_file fixture as parameter
2. Remove try/finally block
3. Use temp_integration_file directly instead of test_file
4. Keep all test assertions unchanged
```

## DATA

### Fixture Return Value

- **Type**: `Generator[Path, None, None]`
- **Yields**: `Path` object pointing to `{project_root}/temp_integration_test.py`

### Test Data Flow

- Fixture provides path → Test writes content → Test runs assertions → Fixture cleans up

## VERIFICATION

```bash
# Run the specific test to verify it works
pytest tests/formatters/test_integration.py::TestQualityGatesValidation::test_complete_tool_integration_workflow -v

# Run all formatter integration tests to ensure no regressions
pytest tests/formatters/test_integration.py -v
```

## CODE CHANGES

### Before (current test structure)

```python
def test_complete_tool_integration_workflow(self) -> None:
    project_root = Path(__file__).parent.parent.parent
    test_file = project_root / "temp_integration_test.py"
    try:
        test_file.write_text(UNFORMATTED_CODE)
        # ... test logic ...
    finally:
        if test_file.exists():
            test_file.unlink()
```

### After (with fixture)

```python
# Fixture (module level, before class)
@pytest.fixture
def temp_integration_file() -> Generator[Path, None, None]:
    """Fixture for temp file in project root with pytest-managed cleanup."""
    project_root = Path(__file__).parent.parent.parent
    test_file = project_root / "temp_integration_test.py"
    yield test_file
    with contextlib.suppress(OSError):
        test_file.unlink(missing_ok=True)

# Test method (inside class)
def test_complete_tool_integration_workflow(self, temp_integration_file: Path) -> None:
    test_file = temp_integration_file
    test_file.write_text(UNFORMATTED_CODE)
    # ... same test logic, no try/finally ...
```
