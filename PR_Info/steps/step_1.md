# Step 1: Setup Project Structure and Data Models

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 1 using TDD: First write comprehensive unit tests for the simplified FormatterResult dataclass, then implement the model to pass the tests. Focus on creating a clean, minimal data structure for formatter results using findings from tool behavior analysis.
```

## WHERE
- `tests/formatters/test_formatter_result.py` - **START HERE: Write unit tests first (TDD)**
- `src/mcp_coder/formatters/__init__.py` - FormatterResult dataclass + package initialization
- `pyproject.toml` - Verify `formatter_integration` pytest marker exists

## WHAT
### Main Functions/Classes
```python
@dataclass
class FormatterResult:
    """Simplified result of running a formatter"""
    success: bool
    files_changed: List[str]  # File paths as strings
    formatter_name: str
    error_message: Optional[str] = None
```

## HOW
### Integration Points
- Verify `formatter_integration` marker exists in pyproject.toml
- Define FormatterResult directly in `__init__.py` for simple API
- Use findings from Step 0 analysis for realistic test scenarios

### Dependencies
```python
from dataclasses import dataclass
from typing import List, Optional
```

## ALGORITHM
```
1. Define simplified FormatterResult dataclass in __init__.py
2. Include basic exports for public API
3. Create comprehensive unit tests covering all scenarios
4. Use Step 0 analysis findings to inform test cases
5. Ensure FormatterResult supports both Black and isort use cases
```

## DATA
### FormatterResult (Simplified)
- `success: bool` - Whether formatting completed successfully
- `files_changed: List[str]` - File paths that were modified (from tool output parsing)
- `formatter_name: str` - Name of formatter used ("black" or "isort")
- `error_message: Optional[str]` - Error details if failed (None for success)

**Removed from original plan:**
- FormatterConfig dataclass (using inline config reading)
- FileChange dataclass (using simple string list)
- execution_time_ms field (not essential for core functionality)

## Tests Required (TDD - Write These First!)
1. **FormatterResult creation and validation**
   - Success with file changes (list of file paths)
   - Success with no changes (empty list)
   - Failure with error message
   - Different formatter names ("black", "isort")

2. **FormatterResult edge cases**
   - None vs empty string for error_message
   - Empty vs populated files_changed list
   - Validation of formatter_name values

3. **FormatterResult usage patterns**
   - Test creation from actual tool output (based on Step 0 findings)
   - Test representation and string formatting
   - Test equality and comparison if needed

4. **Integration readiness**
   - Ensure FormatterResult supports expected usage in formatters
   - Test with realistic file path examples
   - Verify dataclass behavior (repr, equality, etc.)
