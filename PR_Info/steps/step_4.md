# Step 4: Implement Clipboard Utilities

## Objective
Create utilities for clipboard access and commit message validation using tkinter.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and previous steps, implement Step 4: Create clipboard utilities for commit message handling.

Requirements:
- Create clipboard utilities in src/mcp_coder/utils/clipboard.py
- Use tkinter for clipboard access (no external dependencies)
- Implement commit message validation (single line OR multi-line with empty second line)
- Follow existing mcp-coder error handling patterns
- Include comprehensive error handling for clipboard access failures

Focus on robust clipboard access and commit message format validation.
```

## WHERE (File Structure)
```
src/mcp_coder/utils/
├── clipboard.py (new)
└── __init__.py (updated)
```

## WHAT (Functions & Classes)

### `src/mcp_coder/utils/clipboard.py`
```python
def get_clipboard_text() -> tuple[bool, str, Optional[str]]:
    """Get text from clipboard. Returns (success, text, error_message)."""

def validate_commit_message(message: str) -> tuple[bool, Optional[str]]:
    """Validate commit message format. Returns (is_valid, error_message)."""

def parse_commit_message(message: str) -> tuple[str, Optional[str]]:
    """Parse commit message into summary and body. Returns (summary, body)."""
```

### `src/mcp_coder/utils/__init__.py` (updated)
```python
# Add clipboard imports to existing exports
from .clipboard import get_clipboard_text, validate_commit_message, parse_commit_message

__all__ = [
    # ... existing exports ...
    "get_clipboard_text",
    "validate_commit_message", 
    "parse_commit_message",
]
```

## HOW (Integration Points)

### Import Pattern
```python
import tkinter as tk
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)
```

### Error Handling Pattern (following existing utils)
```python
try:
    # clipboard operation
except tk.TclError as e:
    logger.error(f"Clipboard error: {e}")
    return False, "", f"Clipboard access failed: {e}"
```

## ALGORITHM (Core Logic)

### get_clipboard_text()
```
1. Create tkinter root window and withdraw it
2. Try to get clipboard content using root.clipboard_get()
3. Destroy tkinter root window
4. Handle TclError for empty/inaccessible clipboard
5. Return success status, text, and error message
```

### validate_commit_message()
```
1. Strip whitespace and check for empty message
2. Split message into lines
3. Validate: single line OR multi-line with empty second line
4. Check first line length (recommend < 72 chars)
5. Return validation result and specific error message
```

## DATA (Return Values)

### get_clipboard_text() → tuple[bool, str, Optional[str]]
- `(True, "commit message", None)`: Success
- `(False, "", "error message")`: Failure

### validate_commit_message() → tuple[bool, Optional[str]]
- `(True, None)`: Valid format
- `(False, "specific error")`: Invalid with reason

### parse_commit_message() → tuple[str, Optional[str]]
- `("summary", None)`: Single line commit
- `("summary", "body text")`: Multi-line commit

## Tests Required

### `tests/utils/test_clipboard.py`
```python
def test_get_clipboard_text_success(mock_clipboard):
    """Test successful clipboard text retrieval."""

def test_get_clipboard_text_empty():
    """Test handling of empty clipboard."""

def test_get_clipboard_text_error(mock_tkinter_error):
    """Test handling of clipboard access errors."""

def test_validate_commit_message_single_line():
    """Test validation of single line commit messages."""

def test_validate_commit_message_multi_line_valid():
    """Test validation of valid multi-line commit messages."""

def test_validate_commit_message_multi_line_invalid():
    """Test validation of invalid multi-line commit messages."""

def test_parse_commit_message_single_line():
    """Test parsing single line commit message."""

def test_parse_commit_message_multi_line():
    """Test parsing multi-line commit message."""
```

## Validation Rules

### Valid Formats:
1. **Single line**: `"fix: resolve authentication bug"`
2. **Multi-line with empty second line**:
   ```
   feat: add user registration
   
   Implements user signup with email validation and password requirements.
   ```

### Invalid Formats:
1. **Empty message**: `""`
2. **Only whitespace**: `"   "`
3. **Multi-line without empty second line**:
   ```
   feat: add user registration
   Implements user signup with email validation.
   ```

## Error Messages

### Clipboard Errors:
- `"Clipboard is empty"`
- `"Clipboard access failed: {specific_error}"`
- `"No display available for clipboard access"`

### Validation Errors:
- `"Commit message cannot be empty"`
- `"Multi-line commit message must have empty second line"`
- `"Commit summary line too long (recommend < 72 characters)"`

## Acceptance Criteria
1. ✅ Clipboard utilities implemented using tkinter
2. ✅ Robust error handling for all clipboard access scenarios
3. ✅ Commit message validation following git conventions
4. ✅ Support for both single-line and multi-line commit messages
5. ✅ Clear error messages for validation failures
6. ✅ All tests pass with comprehensive coverage
7. ✅ Integration with existing utils module structure
