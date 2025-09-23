# Step 1: Setup Project Structure and Data Models

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 1 using TDD: First write comprehensive unit tests for the ultra-simplified FormatterResult dataclass designed around exit code patterns (0=no changes, 1=changes needed), then implement the model to pass the tests. Use analysis insights to create the minimal data structure that supports proven change detection patterns.
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
    """Ultra-simplified result based on Step 0 analysis patterns"""
    success: bool                    # Based on subprocess exit codes
    files_changed: List[str]         # Files modified (from tool output or exit codes)
    formatter_name: str              # "black" or "isort"
    error_message: Optional[str] = None  # Error details if subprocess failed
```

## HOW
### Integration Points
- Verify `formatter_integration` marker exists in pyproject.toml
- Define FormatterResult directly in `__init__.py` for simple API
- Use Step 0 analysis findings for exit code patterns and test scenarios
- Design to support subprocess.CompletedProcess integration patterns

### Dependencies
```python
from dataclasses import dataclass
from typing import List, Optional
```

## ALGORITHM
```
1. Define ultra-simplified FormatterResult dataclass in __init__.py
2. Include basic exports for public API
3. Create comprehensive unit tests based on Step 0 exit code patterns
4. Test creation from subprocess.CompletedProcess scenarios
5. Test realistic file path scenarios from analysis
6. Ensure FormatterResult supports proven Black and isort integration patterns
```

## DATA
### FormatterResult (Based on Analysis)
- `success: bool` - Whether formatting completed successfully (based on exit codes)
- `files_changed: List[str]` - File paths that were modified (detected via exit codes)
- `formatter_name: str` - Name of formatter used ("black" or "isort")
- `error_message: Optional[str]` - Error details if subprocess failed (None for success)

**Key Analysis Insights Applied:**
- Exit codes provide reliable success/failure detection
- File lists from tools more reliable than custom tracking
- Simple string paths sufficient (no complex objects needed)
- Error messages from subprocess stderr when exit != 0 or 1

## Tests Required (TDD - Write These First!)
1. **FormatterResult creation based on analysis patterns**
   - Success with file changes (exit code 1 → changes made)
   - Success with no changes (exit code 0 → no changes)
   - Failure with error message (exit code 123+ → error)
   - Different formatter names ("black", "isort")

2. **FormatterResult exit code scenarios**
   - Test creation from subprocess results (returncode 0, 1, 123)
   - Test error message extraction from stderr
   - Test file path lists from different sources
   - Validation of formatter_name values

3. **FormatterResult usage patterns from analysis**
   - Test creation from actual Black tool scenarios (Step 0 examples)
   - Test creation from actual isort tool scenarios (Step 0 examples)
   - Test representation and string formatting
   - Test equality and comparison for testing

4. **Integration readiness for proven patterns**
   - Ensure FormatterResult supports exit code → success mapping
   - Test with realistic file path examples from analysis
   - Test compatibility with subprocess.CompletedProcess patterns
   - Verify dataclass behavior (repr, equality, etc.)
