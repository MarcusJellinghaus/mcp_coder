# Step 1: Improve Black formatter error handling and add debug logging

## LLM Prompt

```
Implement Step 1 of Issue #314: Improve Black formatter error handling.

Reference: pr_info/steps/summary.md for full context.

Tasks:
1. Include stderr output in the error_message when Black fails (so users can see which file has errors)
2. Add DEBUG logging for the full command before execution
```

## WHERE

| File | Action |
|------|--------|
| `tests/formatters/test_black_formatter.py` | Add tests for improved error handling |
| `src/mcp_coder/formatters/black_formatter.py` | Add logging + include stderr in error_message |

## WHAT

### Production Code Changes

```python
# At top of file, add:
import logging

logger = logging.getLogger(__name__)

# In _format_black_directory(), before execute_command():
logger.debug("Black command: %s", command)

# In format_with_black() except block, replace current error handling:
except subprocess.CalledProcessError as e:
    # Include the actual stderr output from Black for better debugging
    # CalledProcessError stores output in 'output' attr when using 3-arg form
    stderr_output = getattr(e, "output", "") or getattr(e, "stderr", "") or ""
    error_details = f"{e}\nOutput: {stderr_output}" if stderr_output else str(e)
    return FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="black",
        error_message=f"Black formatting error: {error_details}",
    )
except (FileNotFoundError, OSError) as e:
    return FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="black",
        error_message=f"Black formatting error: {str(e)}",
    )
```

## HOW

### Integration Points
- Import `logging` module (standard library)
- Create module-level logger using `__name__`
- Log full command at DEBUG level before execution
- Extract stderr from `CalledProcessError` and include in error_message

### Key Insight
`subprocess.CalledProcessError` with 3-argument form stores the output in `e.output`, not `e.stderr`. The code currently uses:
```python
raise subprocess.CalledProcessError(result.return_code, command, result.stderr)
```
This means `result.stderr` becomes `e.output`. We handle both attributes for safety.

## ALGORITHM

```
1. Import logging, create logger at module level
2. In _format_black_directory():
   - Log DEBUG with full command before execute_command()
3. In format_with_black() except block:
   - Separate CalledProcessError handling from other exceptions
   - Extract stderr from e.output or e.stderr (whichever exists)
   - Include stderr in the error_message for visibility
```

## DATA

### Input
- `subprocess.CalledProcessError` with stderr in `output` attribute

### Output
- `FormatterResult` with `error_message` containing the actual stderr output
- Side effect: DEBUG log with full command

### Error Message Format (improved)
```
Black formatting error: Command '['black', ...]' returned non-zero exit status 123.
Output: error: cannot format src/broken.py: Cannot parse: 1:0: ...
```

## TEST IMPLEMENTATION

### Test 1: Error message includes stderr

```python
def test_format_directory_error_includes_stderr(
    self, temp_project_dir: Path, monkeypatch: Any
) -> None:
    """Test that stderr output is included in error_message when Black fails."""
    from mcp_coder.formatters.black_formatter import format_with_black

    # Create a directory structure
    src_dir = temp_project_dir / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("x = 1")

    # Mock execute_command to simulate Black syntax error with stderr
    mock_result = Mock()
    mock_result.return_code = 123
    mock_result.stdout = ""
    mock_result.stderr = "error: cannot format broken.py: Cannot parse: 1:0: invalid syntax"

    monkeypatch.setattr(
        "mcp_coder.formatters.black_formatter.execute_command",
        lambda cmd: mock_result,
    )

    result = format_with_black(temp_project_dir)

    # Verify failure
    assert result.success is False
    assert result.formatter_name == "black"
    
    # Verify stderr is included in error_message
    assert "cannot format broken.py" in result.error_message
    assert "invalid syntax" in result.error_message
```

### Test 2: Debug logging for command

```python
def test_format_directory_logs_command_at_debug(
    self, temp_project_dir: Path, monkeypatch: Any, caplog: Any
) -> None:
    """Test that the full Black command is logged at DEBUG level."""
    import logging
    from mcp_coder.formatters.black_formatter import format_with_black

    # Create a directory structure
    src_dir = temp_project_dir / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("x = 1")

    # Mock execute_command to return success
    mock_result = Mock()
    mock_result.return_code = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    monkeypatch.setattr(
        "mcp_coder.formatters.black_formatter.execute_command",
        lambda cmd: mock_result,
    )

    # Capture DEBUG logs
    with caplog.at_level(logging.DEBUG, logger="mcp_coder.formatters.black_formatter"):
        format_with_black(temp_project_dir)

    # Verify command was logged
    assert any("Black command:" in record.message for record in caplog.records)
    assert any("--line-length" in record.message for record in caplog.records)
```

## VERIFICATION

After implementation, run:
```bash
python -m pytest tests/formatters/test_black_formatter.py -v
```
