# Step 1: Add `_format_toml_error()` Helper Function

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

Add a helper function `_format_toml_error()` in `user_config.py` that formats 
TOML parse errors in Python's SyntaxError style. Follow TDD - write tests first.
```

## WHERE

- **Test file**: `tests/utils/test_user_config.py`
- **Implementation file**: `src/mcp_coder/utils/user_config.py`

## WHAT

### Function Signature

```python
def _format_toml_error(file_path: Path, error: tomllib.TOMLDecodeError) -> str:
    """Format TOML parse error in Python SyntaxError style.
    
    Args:
        file_path: Path to the config file that failed to parse
        error: The TOMLDecodeError from tomllib
        
    Returns:
        Formatted error string with file path, line content, and pointer
    """
```

### Expected Output Format

```
  File "C:\Users\me\.mcp_coder\config.toml", line 25
    executor_os = "linux
                       ^
TOML parse error: Illegal character '\n'
```

## HOW

### Integration Points

- Private helper function (underscore prefix)
- Called by `load_config()` in Step 2
- No decorator needed

### Imports to Add

```python
import re  # For parsing line/column from error message
```

## ALGORITHM

```
1. Extract line number and column from error message using regex
2. Read file content and get the error line (handle file read errors gracefully)
3. Build pointer string with spaces + caret at column position
4. Format output: File line, content line, pointer line, error message line
5. Return formatted string
```

## DATA

### Input

- `file_path`: `Path` object pointing to config file
- `error`: `tomllib.TOMLDecodeError` with message like `"Illegal character '\n' (at line 25, column 49)"`

### Output

- `str`: Multi-line formatted error message

### Error Message Patterns

The `tomllib.TOMLDecodeError` message format:
- `"Illegal character '\n' (at line 25, column 49)"`
- `"Expected '=' after a key (at line 10, column 1)"`

Regex pattern: `r"\(at line (\d+), column (\d+)\)"`

## TESTS TO WRITE

### Test Class: `TestFormatTomlError`

```python
class TestFormatTomlError:
    """Tests for _format_toml_error helper function."""

    def test_format_includes_file_path(self, tmp_path):
        """Error message includes the file path."""
        
    def test_format_includes_line_number(self, tmp_path):
        """Error message includes line number from error."""
        
    def test_format_includes_error_line_content(self, tmp_path):
        """Error message includes the actual line content."""
        
    def test_format_includes_pointer_at_column(self, tmp_path):
        """Error message includes ^ pointer at error column."""
        
    def test_format_handles_file_read_error(self, tmp_path):
        """Gracefully handles if file cannot be read for context."""
        
    def test_format_handles_line_out_of_range(self, tmp_path):
        """Handles when error line number exceeds file lines."""
```

## IMPLEMENTATION NOTES

1. Column position in error is 1-based, adjust for 0-based string indexing
2. If file can't be read for context, still show file path and error message
3. If line number exceeds file length, show error without line content
4. Strip trailing whitespace from error line for cleaner output
