# Step 4: Update Tests in test_data_files.py

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 4.
Update test_data_files.py to use pytest's caplog fixture instead of structlog.testing.LogCapture.
Remove structlog imports from the test file.
```

## WHERE
- **File**: `tests/utils/test_data_files.py`

## WHAT

### Import Changes
| Line | Before | After |
|------|--------|-------|
| 10 | `import structlog` | (remove) |
| 11 | `from structlog.testing import LogCapture` | (remove) |

### Test Method Updates

Three test methods use `structlog.testing.LogCapture`:
1. `test_data_file_found_logs_debug_not_info`
2. `test_data_file_logging_with_info_level`
3. `test_data_file_logging_with_debug_level`

All need conversion from `LogCapture` to pytest's `caplog` fixture.

## HOW

### Before (structlog LogCapture pattern)
```python
def test_data_file_found_logs_debug_not_info(self) -> None:
    # ... setup ...
    cap = LogCapture()
    structlog.configure(processors=[cap])
    
    # ... call function ...
    
    logged_messages = cap.entries
    success_messages = [
        msg for msg in logged_messages
        if "Found data file" in msg.get("event", "")
    ]
    assert success_messages[0]["log_level"] == "debug"
```

### After (pytest caplog pattern)
```python
def test_data_file_found_logs_debug_not_info(self, caplog: pytest.LogCaptureFixture) -> None:
    # ... setup ...
    
    with caplog.at_level(logging.DEBUG):
        # ... call function ...
    
    success_messages = [
        record for record in caplog.records
        if "Found data file" in record.message
    ]
    assert success_messages[0].levelname == "DEBUG"
```

## ALGORITHM

```python
# Conversion pattern for each test:
1. Add caplog parameter to test method signature
2. Remove LogCapture() and structlog.configure() lines
3. Wrap function call in: with caplog.at_level(logging.DEBUG):
4. Change cap.entries to caplog.records
5. Change msg.get("event", "") to record.message
6. Change msg["log_level"] to record.levelname (uppercase: "DEBUG" not "debug")
```

## DATA

### LogCapture Entry Format (Before)
```python
{
    "event": "Found data file in installed package (via importlib)",
    "log_level": "debug",
    "method": "importlib_spec",
    "path": "/path/to/file"
}
```

### caplog Record Format (After)
```python
LogRecord(
    message="Found data file in installed package (via importlib)",
    levelname="DEBUG",
    # extra fields accessible via record.__dict__ if needed
)
```

## TEST METHODS TO UPDATE

### 1. test_data_file_found_logs_debug_not_info
```python
def test_data_file_found_logs_debug_not_info(self, caplog: pytest.LogCaptureFixture) -> None:
    """Test that successful data file discovery logs at debug level."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / "test_package"
        test_file = package_dir / "data" / "test_script.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test script")

        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")

        with caplog.at_level(logging.DEBUG):
            with patch(
                "mcp_coder.utils.data_files.importlib.util.find_spec",
                return_value=mock_spec,
            ):
                result = find_data_file(
                    package_name="test_package",
                    relative_path="data/test_script.py",
                    development_base_dir=None,
                )

                assert result == test_file

        success_messages = [
            record for record in caplog.records
            if "Found data file in installed package (via importlib)" in record.message
        ]
        assert len(success_messages) == 1
        assert success_messages[0].levelname == "DEBUG"
```

### 2. test_data_file_logging_with_info_level
Similar conversion - verify no success messages at INFO level.

### 3. test_data_file_logging_with_debug_level
Similar conversion - verify messages appear at DEBUG level.

## IMPLEMENTATION CHECKLIST

- [ ] Remove `import structlog` from imports
- [ ] Remove `from structlog.testing import LogCapture` from imports
- [ ] Add `import logging` if not present
- [ ] Update `test_data_file_found_logs_debug_not_info` to use caplog
- [ ] Update `test_data_file_logging_with_info_level` to use caplog
- [ ] Update `test_data_file_logging_with_debug_level` to use caplog
- [ ] Run tests: `pytest tests/utils/test_data_files.py -v`
