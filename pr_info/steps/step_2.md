# Step 2: Add stderr debug logging to isort formatter

## LLM Prompt

```
Implement Step 2 of Issue #314: Add stderr debug logging to isort formatter.

Reference: pr_info/steps/summary.md for full context.

Task: When isort fails with a non-zero exit code, log the stderr output at DEBUG level
so developers can see which file caused the error. This mirrors Step 1 for Black.
```

## WHERE

| File | Action |
|------|--------|
| `tests/formatters/test_isort_formatter.py` | Add test for stderr logging |
| `src/mcp_coder/formatters/isort_formatter.py` | Add logging import and DEBUG log |

## WHAT

### Test Function (add to `TestIsortFormatterCore`)

```python
def test_format_error_logs_stderr_on_failure(
    self, temp_project_dir: Path, import_error_code: str, monkeypatch: Any, caplog: Any
) -> None:
    """Test that stderr is logged at DEBUG level when isort fails."""
```

### Production Code Changes

```python
# At top of file, add:
import logging

logger = logging.getLogger(__name__)

# In except block of format_with_isort(), add before return:
if isinstance(e, subprocess.CalledProcessError) and e.stderr:
    logger.debug("isort stderr output: %s", e.stderr)
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
2. In format_with_isort() except block:
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
DEBUG - isort stderr output: ERROR: Could not parse syntax in edge_case.py
```

## TEST IMPLEMENTATION

```python
def test_format_error_logs_stderr_on_failure(
    self, temp_project_dir: Path, import_error_code: str, monkeypatch: Any, caplog: Any
) -> None:
    """Test that stderr is logged at DEBUG level when isort fails."""
    import logging
    from mcp_coder.formatters.isort_formatter import format_with_isort
    from mcp_coder.utils.subprocess_runner import CommandResult

    # Create a Python file with problematic import syntax
    test_file = temp_project_dir / "edge_case.py"
    test_file.write_text(import_error_code)

    # Mock execute_command to simulate isort syntax error with stderr
    mock_result = CommandResult(
        return_code=123,
        stdout="",
        stderr="ERROR: Could not parse syntax in edge_case.py",
        timed_out=False,
    )
    monkeypatch.setattr(
        "mcp_coder.formatters.isort_formatter.execute_command",
        lambda cmd: mock_result,
    )

    # Capture DEBUG logs
    with caplog.at_level(logging.DEBUG, logger="mcp_coder.formatters.isort_formatter"):
        result = format_with_isort(temp_project_dir)

    # Verify failure
    assert result.success is False

    # Verify stderr was logged at DEBUG level
    assert any("isort stderr output" in record.message for record in caplog.records)
    assert any("Could not parse" in record.message for record in caplog.records)
```

## VERIFICATION

After implementation, run:
```bash
python -m pytest tests/formatters/test_isort_formatter.py -v -k "test_format_error_logs_stderr"
```
