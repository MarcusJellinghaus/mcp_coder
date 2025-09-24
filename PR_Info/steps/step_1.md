# Step 1: Setup Project Structure and Data Models

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 1 using TDD: First write comprehensive unit tests for the ultra-simplified FormatterResult dataclass designed around exit code patterns (0=no changes, 1=changes needed), then implement the model to pass the tests. Use analysis insights to create the minimal data structure that supports proven change detection patterns.
```

## WHERE
- `tests/formatters/test_models.py` - **START HERE: Write 2 FormatterResult tests first (TDD)**
- `tests/formatters/test_config_reader.py` - **THEN: Write 3 configuration tests (TDD)**
- `src/mcp_coder/formatters/models.py` - FormatterResult dataclass
- `src/mcp_coder/formatters/config_reader.py` - Configuration reading + line-length warning
- `src/mcp_coder/formatters/__init__.py` - Package exports
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

## Tests Required (TDD - Write 6 Tests First!)
1. **FormatterResult creation scenarios (2 tests)**
   - Success with changes: `FormatterResult(success=True, files_changed=["file.py"], formatter_name="black")`
   - Failure with error: `FormatterResult(success=False, files_changed=[], formatter_name="black", error_message="syntax error")`

2. **Configuration reading (2 tests)**
   - Found configuration: Read `[tool.black]` and `[tool.isort]` from pyproject.toml
   - Missing configuration: Return defaults when sections not found

3. **Line-length conflict warning (1 test)**
   - Conflict detection: Black line-length=100, isort line_length=88 → warning message

4. **Integration readiness (1 test)**
   - Exit code mapping: Verify FormatterResult supports subprocess.CompletedProcess integration patterns
