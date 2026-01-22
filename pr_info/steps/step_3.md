# Step 3: Add early exit on formatter failure in format_code()

## LLM Prompt

```
Implement Step 3 of Issue #314: Add early exit on formatter failure in format_code().

Reference: pr_info/steps/summary.md for full context.

Task: When a formatter fails in the format_code() loop, log at INFO level immediately
and break out of the loop early (don't run subsequent formatters).
```

## WHERE

| File | Action |
|------|--------|
| `tests/formatters/test_main_api.py` | Update test + add new test for early exit |
| `src/mcp_coder/formatters/__init__.py` | Add logging import and early exit logic |

## WHAT

### Test Function (add to `TestCombinedAPICoreFunctionality`)

```python
def test_format_code_early_exit_on_failure(
    self, mock_isort: Mock, mock_black: Mock, caplog: Any
) -> None:
    """Test that format_code() exits early and logs when a formatter fails."""
```

### Update Existing Test

The existing test `test_format_code_error_handling_one_formatter_fails` needs updating:
- Currently expects isort to run even when Black fails
- Should be updated to expect early exit (isort NOT called)

### Production Code Changes

```python
# At top of file, add:
import logging

logger = logging.getLogger(__name__)

# In format_code() loop, after each formatter result:
if formatter_name == "black":
    results["black"] = format_with_black(project_root, target_dirs)
    if not results["black"].success:
        logger.info(
            "%s formatting failed: %s",
            results["black"].formatter_name,
            results["black"].error_message,
        )
        break
elif formatter_name == "isort":
    results["isort"] = format_with_isort(project_root, target_dirs)
    if not results["isort"].success:
        logger.info(
            "%s formatting failed: %s",
            results["isort"].formatter_name,
            results["isort"].error_message,
        )
        break
```

## HOW

### Integration Points
- Import `logging` module (standard library)
- Create module-level logger using `__name__`
- Add early exit check after each formatter execution
- Log at INFO level when a formatter fails

### Test Integration
- Use pytest's `caplog` fixture to capture log output
- Mock both formatters
- Verify isort is NOT called when Black fails
- Verify INFO log message is emitted

## ALGORITHM

```
1. Import logging, create logger at module level
2. In format_code() for each formatter:
3.   Run formatter, store result
4.   IF result.success is False:
5.     Log INFO with formatter name and error message
6.     Break out of loop (don't run remaining formatters)
7. Return results dict (may contain only failed formatter)
```

## DATA

### Input
- `FormatterResult` with `success=False` and `error_message`

### Output
- Dict with only the formatters that ran (failed formatter is last)
- Side effect: INFO log message when failure occurs

### Log Format
```
INFO - black formatting failed: Black formatting error: Command ... returned non-zero exit status 123
```

## TEST IMPLEMENTATION

### New Test: Early Exit Behavior

```python
@patch("mcp_coder.formatters.format_with_black")
@patch("mcp_coder.formatters.format_with_isort")
def test_format_code_early_exit_on_failure(
    self, mock_isort: Mock, mock_black: Mock, caplog: Any
) -> None:
    """Test that format_code() exits early and logs when a formatter fails."""
    import logging

    # Setup - Black fails
    mock_black.return_value = FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="black",
        error_message="Black formatting error: syntax error in file.py",
    )

    from mcp_coder.formatters import format_code

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)

        # Capture INFO logs
        with caplog.at_level(logging.INFO, logger="mcp_coder.formatters"):
            result = format_code(project_root)

        # Verify Black was called
        mock_black.assert_called_once()

        # Verify isort was NOT called (early exit)
        mock_isort.assert_not_called()

        # Verify result contains only black (failed)
        assert "black" in result
        assert "isort" not in result
        assert result["black"].success is False

        # Verify INFO log was emitted
        assert any("black formatting failed" in record.message for record in caplog.records)
```

### Update Existing Test

Change `test_format_code_error_handling_one_formatter_fails` to reflect new behavior:

```python
@patch("mcp_coder.formatters.format_with_black")
@patch("mcp_coder.formatters.format_with_isort")
def test_format_code_error_handling_one_formatter_fails(
    self, mock_isort: Mock, mock_black: Mock
) -> None:
    """Test when Black fails, isort does NOT run (early exit behavior)."""
    # Setup - Black fails on directory processing
    mock_black.return_value = FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="black",
        error_message="Black failed",
    )

    from mcp_coder.formatters import format_code

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)

        result = format_code(project_root)

        # Verify Black was called
        mock_black.assert_called_once_with(project_root, None)

        # Verify isort was NOT called (early exit)
        mock_isort.assert_not_called()

        # Verify result contains only black
        assert isinstance(result, dict)
        assert "black" in result
        assert "isort" not in result
        assert result["black"].success is False
        assert result["black"].error_message == "Black failed"
```

## VERIFICATION

After implementation, run:
```bash
python -m pytest tests/formatters/test_main_api.py -v -k "test_format_code"
```
