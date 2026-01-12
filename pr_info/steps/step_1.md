# Step 1: Update Console Formatter in log_utils.py

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 1.
Add an ExtraFieldsFormatter class to log_utils.py that displays extra fields in console output.
Follow TDD: write test first, then implement.
```

## WHERE
- **Test file**: `tests/utils/test_log_utils.py`
- **Implementation file**: `src/mcp_coder/utils/log_utils.py`

## WHAT

### New Class: `ExtraFieldsFormatter`
```python
class ExtraFieldsFormatter(logging.Formatter):
    """Formatter that appends extra fields to log messages."""
    
    def format(self, record: logging.LogRecord) -> str:
        ...
```

### Modified Function: `setup_logging`
Update console handler creation to use `ExtraFieldsFormatter` instead of basic `Formatter`.

## HOW

### Integration Points
1. `ExtraFieldsFormatter` inherits from `logging.Formatter`
2. Replace `logging.Formatter(...)` with `ExtraFieldsFormatter(...)` in console setup section
3. No changes to file/JSON logging (already works)

## ALGORITHM

```python
# ExtraFieldsFormatter.format() pseudocode:
def format(self, record):
    base_message = super().format(record)
    extra_fields = get_non_standard_fields(record)
    if extra_fields:
        # Decision 1: Use JSON object format with json.dumps()
        suffix = json.dumps(extra_fields)
        return f"{base_message} {suffix}"
    return base_message
```

### Standard LogRecord Fields to Exclude
```python
STANDARD_FIELDS = {
    'name', 'msg', 'args', 'created', 'filename', 'funcName',
    'levelname', 'levelno', 'lineno', 'module', 'msecs',
    'pathname', 'process', 'processName', 'relativeCreated',
    'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
    'taskName', 'message'
}
```

## DATA

### Input
- `logging.LogRecord` with optional `extra` fields

### Output
- Formatted string: `"2024-01-15 10:30:00 - module - INFO - Message {"key1": "val1", "key2": 42}"`

## TEST CASES

```python
# tests/utils/test_log_utils.py - Add new test class

class TestExtraFieldsFormatter:
    """Tests for ExtraFieldsFormatter class."""

    def test_format_without_extra_fields(self) -> None:
        """Test formatting a log record with no extra fields."""
        # Standard message should remain unchanged
        
    def test_format_with_extra_fields(self) -> None:
        """Test formatting a log record with extra fields."""
        # Extra fields should be appended as [key=value]
        
    def test_format_with_multiple_extra_fields(self) -> None:
        """Test formatting with multiple extra fields."""
        # All extra fields should be included
```

## IMPLEMENTATION CHECKLIST

- [ ] Add test class `TestExtraFieldsFormatter` to `tests/utils/test_log_utils.py`
- [ ] Add `STANDARD_LOG_FIELDS` constant to `log_utils.py`
- [ ] Add `ExtraFieldsFormatter` class to `log_utils.py`
- [ ] Update `setup_logging()` console handler to use `ExtraFieldsFormatter`
- [ ] Run tests: `pytest tests/utils/test_log_utils.py -v`
