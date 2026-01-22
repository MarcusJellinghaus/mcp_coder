# Step 2: Improve isort formatter error handling and add debug logging

## LLM Prompt

```
Implement Step 2 of Issue #314: Improve isort formatter error handling.

Reference: pr_info/steps/summary.md for full context.

Tasks:
1. Include stderr output in the error_message when isort fails (so users can see which file has errors)
2. Add DEBUG logging for the full command before execution

This mirrors Step 1 for the isort formatter.
```

## WHERE

| File | Action |
|------|--------|
| `tests/formatters/test_isort_formatter.py` | Add tests for improved error handling |
| `src/mcp_coder/formatters/isort_formatter.py` | Add logging + include stderr in error_message |

## WHAT

### Production Code Changes

```python
# At top of file, add:
import logging

logger = logging.getLogger(__name__)

# In _format_isort_directory(), before execute_command():
logger.debug("isort command: %s", command)

# In format_with_isort() except block, replace current error handling:
except subprocess.CalledProcessError as e:
    # Include the actual stderr output from isort for better debugging
    # CalledProcessError stores output in 'output' attr when using 3-arg form
    stderr_output = getattr(e, "output", "") or getattr(e, "stderr", "") or ""
    error_details = f"{e}\nOutput: {stderr_output}" if stderr_output else str(e)
    return FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="isort",
        error_message=f"isort formatting error: {error_details}",
    )
except OSError as e:
    return FormatterResult(
        success=False,
        files_changed=[],
        formatter_name="isort",
        error_message=f"isort formatting error: {str(e)}",
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
2. In _format_isort_directory():
   - Log DEBUG with full command before execute_command()
3. In format_with_isort() except block:
   - Separate CalledProcessError handling from OSError
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
isort formatting error: Command '['isort', ...]' returned non-zero exit status 1.
Output: ERROR: Could not parse syntax in edge_case.py
```

## TEST IMPLEMENTATION

### Test 1: Error message includes stderr

```python
def test_format_directory_error_includes_stderr(
    self, temp_project_dir: Path, monkeypatch: Any
) -> None:
    """Test that stderr output is included in error_message when isort fails."""
    from mcp_coder.formatters.isort_formatter import format_with_isort

    # Create a directory structure
    src_dir = temp_project_dir / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("import os")

    # Mock execute_command to simulate isort error with stderr
    mock_result = Mock()
    mock_result.return_code = 1
    mock_result.stdout = ""
    mock_result.stderr = "ERROR: Could not parse syntax in edge_case.py"

    monkeypatch.setattr(
        "mcp_coder.formatters.isort_formatter.execute_command",
        lambda cmd: mock_result,
    )

    result = format_with_isort(temp_project_dir)

    # Verify failure
    assert result.success is False
    assert result.formatter_name == "isort"
    
    # Verify stderr is included in error_message
    assert "Could not parse syntax" in result.error_message
    assert "edge_case.py" in result.error_message
```

### Test 2: Debug logging for command

```python
def test_format_directory_logs_command_at_debug(
    self, temp_project_dir: Path, monkeypatch: Any, caplog: Any
) -> None:
    """Test that the full isort command is logged at DEBUG level."""
    import logging
    from mcp_coder.formatters.isort_formatter import format_with_isort

    # Create a directory structure
    src_dir = temp_project_dir / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("import os")

    # Mock execute_command to return success
    mock_result = Mock()
    mock_result.return_code = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    monkeypatch.setattr(
        "mcp_coder.formatters.isort_formatter.execute_command",
        lambda cmd: mock_result,
    )

    # Capture DEBUG logs
    with caplog.at_level(logging.DEBUG, logger="mcp_coder.formatters.isort_formatter"):
        format_with_isort(temp_project_dir)

    # Verify command was logged
    assert any("isort command:" in record.message for record in caplog.records)
    assert any("--profile" in record.message for record in caplog.records)
```

## VERIFICATION

After implementation, run:
```bash
python -m pytest tests/formatters/test_isort_formatter.py -v
```
