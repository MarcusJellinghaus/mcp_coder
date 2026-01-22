# Step 1: Add stderr debug logging to Black formatter

## LLM Prompt

```
Implement Step 1 of Issue #314: Add stderr debug logging to Black formatter.

Reference: pr_info/steps/summary.md for full context.

Task: When Black fails with a non-zero exit code, log the stderr output at DEBUG level
so developers can see which file caused the error.
```

## WHERE

| File | Action |
|------|--------|
| `tests/formatters/test_black_formatter.py` | Add test for stderr logging |
| `src/mcp_coder/formatters/black_formatter.py` | Add logging import and DEBUG log |

## WHAT

### Test Function (add to `TestBlackFormatterCore`)

```python
def test_format_directory_logs_stderr_on_failure(
    self, temp_project_dir: Path, syntax_error_code: str, monkeypatch: Any, caplog: Any
) -> None:
    """Test that stderr is logged at DEBUG level when Black fails."""
```

### Production Code Changes

```python
# At top of file, add:
import logging

logger = logging.getLogger(__name__)

# In except block of format_with_black(), add before return:
if isinstance(e, subprocess.CalledProcessError) and e.stderr:
    logger.debug("Black stderr output: %s", e.stderr)
```

## HOW

### Integration Points
- Import `logging` module (standard library)
- Create module-level logger using `__name__`
- Log in `except` block before returning `FormatterResult`

### Test Integration
- Use pytest's `caplog` fixture to capture log output
- Set log level to DEBUG to capture the message
- Assert the stderr content appears in captured logs

## ALGORITHM

```
1. Import logging, create logger at module level
2. In format_with_black() except block:
3.   IF exception is CalledProcessError AND has stderr:
4.     Log stderr at DEBUG level
5.   Return FormatterResult (unchanged)
```

## DATA

### Input
- `subprocess.CalledProcessError` with `stderr` attribute containing error details

### Output
- No change to return value
- Side effect: DEBUG log message with stderr content

### Log Format
```
DEBUG - Black stderr output: error: cannot format src/broken.py: Cannot parse: 1:0: ...
```

## TEST IMPLEMENTATION

```python
def test_format_directory_logs_stderr_on_failure(
    self, temp_project_dir: Path, syntax_error_code: str, monkeypatch: Any, caplog: Any
) -> None:
    """Test that stderr is logged at DEBUG level when Black fails."""
    import logging
    from mcp_coder.formatters.black_formatter import format_with_black
    from unittest.mock import Mock

    # Create a Python file with syntax errors
    src_dir = temp_project_dir / "src"
    src_dir.mkdir()
    test_file = src_dir / "broken_module.py"
    test_file.write_text(syntax_error_code)

    # Mock execute_command to simulate Black syntax error with stderr
    mock_result = Mock()
    mock_result.return_code = 123
    mock_result.stdout = ""
    mock_result.stderr = "error: cannot format broken_module.py: Cannot parse: 1:0"

    monkeypatch.setattr(
        "mcp_coder.formatters.black_formatter.execute_command",
        lambda cmd: mock_result,
    )

    # Capture DEBUG logs
    with caplog.at_level(logging.DEBUG, logger="mcp_coder.formatters.black_formatter"):
        result = format_with_black(temp_project_dir)

    # Verify failure
    assert result.success is False

    # Verify stderr was logged at DEBUG level
    assert any("Black stderr output" in record.message for record in caplog.records)
    assert any("cannot format" in record.message for record in caplog.records)
```

## VERIFICATION

After implementation, run:
```bash
python -m pytest tests/formatters/test_black_formatter.py -v -k "test_format_directory_logs_stderr"
```
