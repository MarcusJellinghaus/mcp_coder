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
| `tests/formatters/test_main_api.py` | Update existing test + add new test for early exit |
| `src/mcp_coder/formatters/__init__.py` | Add logging import and early exit logic |

## WHAT

### Production Code Changes

```python
# At top of file, add:
import logging

logger = logging.getLogger(__name__)

# In format_code() loop, add early exit check after each formatter:
for formatter_name in formatters:
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

return results
```

## HOW

### Integration Points
- Import `logging` module (standard library)
- Create module-level logger using `__name__`
- Add early exit check after each formatter execution
- Log at INFO level when a formatter fails (includes stderr from Steps 1-2)

### Behavior Change
- **Before**: All formatters run regardless of failures
- **After**: Stop at first failure, return partial results

## ALGORITHM

```
1. Import logging, create logger at module level
2. In format_code() for each formatter:
3.   Run formatter, store result
4.   IF result.success is False:
5.     Log INFO with formatter name and error_message (now includes stderr)
6.     Break out of loop (don't run remaining formatters)
7. Return results dict (may contain only failed formatter)
```

## DATA

### Input
- `FormatterResult` with `success=False` and `error_message` (now includes stderr)

### Output
- Dict with only the formatters that ran (failed formatter is last)
- Side effect: INFO log message when failure occurs

### Log Format
```
INFO - black formatting failed: Black formatting error: Command '['black', ...]' returned non-zero exit status 123.
Output: error: cannot format src/broken.py: Cannot parse: 1:0: ...
```

## TEST IMPLEMENTATION

### Test 1: Early Exit Behavior (New Test)

```python
@patch("mcp_coder.formatters.format_with_black")
@patch("mcp_coder.formatters.format_with_isort")
def test_format_code_early_exit_on_failure(
    self, mock_isort: Mock, mock_black: Mock, caplog: Any
) -> None:
    """Test that format_code() exits early and logs when a formatter fails."""
    import logging

    # Setup - Black fails with detailed error message
    mock_black.return_value = FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="black",
        error_message="Black formatting error: Command ... returned non-zero exit status 123.\nOutput: error: cannot format file.py",
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

        # Verify INFO log was emitted with error details
        assert any("black formatting failed" in record.message for record in caplog.records)
        assert any("cannot format file.py" in record.message for record in caplog.records)
```

### Test 2: Update Existing Test

Change `test_format_code_error_handling_one_formatter_fails` to reflect new early exit behavior:

```python
@patch("mcp_coder.formatters.format_with_black")
@patch("mcp_coder.formatters.format_with_isort")
def test_format_code_error_handling_one_formatter_fails(
    self, mock_isort: Mock, mock_black: Mock
) -> None:
    """Test when Black fails, isort does NOT run (early exit behavior)."""
    # Setup - Black fails
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

### Test 3: isort Failure Also Triggers Early Exit

```python
@patch("mcp_coder.formatters.format_with_black")
@patch("mcp_coder.formatters.format_with_isort")
def test_format_code_early_exit_on_isort_failure(
    self, mock_isort: Mock, mock_black: Mock, caplog: Any
) -> None:
    """Test that format_code() exits early when isort fails (after Black succeeds)."""
    import logging

    # Setup - Black succeeds, isort fails
    mock_black.return_value = FormatterResult(
        success=True,
        files_changed=["file.py"],
        formatter_name="black",
        error_message=None,
    )
    mock_isort.return_value = FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="isort",
        error_message="isort formatting error: Could not parse",
    )

    from mcp_coder.formatters import format_code

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)

        with caplog.at_level(logging.INFO, logger="mcp_coder.formatters"):
            result = format_code(project_root)

        # Verify both were called (Black succeeded, isort failed)
        mock_black.assert_called_once()
        mock_isort.assert_called_once()

        # Verify result contains both
        assert "black" in result
        assert "isort" in result
        assert result["black"].success is True
        assert result["isort"].success is False

        # Verify INFO log was emitted for isort failure
        assert any("isort formatting failed" in record.message for record in caplog.records)
```

## VERIFICATION

After implementation, run:
```bash
python -m pytest tests/formatters/test_main_api.py -v -k "test_format_code"
```
