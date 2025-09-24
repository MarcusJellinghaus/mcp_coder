# Step 3: Fix Data Files Log Level from Info to Debug

## Objective
Change the specific log message "Found data file in installed package (via importlib)" from `info` to `debug` level in `data_files.py` so it only appears when `--log-level DEBUG` is used.

## WHERE
- **File**: `src/mcp_coder/utils/data_files.py`
- **Function**: `find_data_file()` - Method 2/5 success case
- **Line**: Around line 150-160 (the `structured_logger.info()` call)
- **Test File**: `tests/utils/test_data_files.py` (extend existing)

## WHAT
### Main Functions with Signatures
```python
# NO function signature changes
# ONLY internal logging level change in existing find_data_file() function
```

### Test Functions
```python
def test_data_file_found_logs_debug_not_info():
    """Test that successful data file discovery logs at debug level."""
    
def test_data_file_logging_with_info_level():
    """Test that data file messages don't appear at INFO level."""
    
def test_data_file_logging_with_debug_level():
    """Test that data file messages appear at DEBUG level."""
```

## HOW
### Integration Points
- **Modify**: ONE line in `data_files.py` 
- **Change**: `structured_logger.info(` → `structured_logger.debug(`
- **Location**: Method 2/5 success case in `find_data_file()` function
- **Specific Message**: "Found data file in installed package (via importlib)"

### Exact Change Required
```python
# Before (around line 150-160)
structured_logger.info(
    "Found data file in installed package (via importlib)",
    method="importlib_spec", 
    path=str(installed_file_absolute),
)

# After
structured_logger.debug(
    "Found data file in installed package (via importlib)",
    method="importlib_spec",
    path=str(installed_file_absolute), 
)
```

## ALGORITHM
```
1. Locate find_data_file() function in data_files.py
2. Find "METHOD 2/5" section (importlib search)
3. Find the success case with "Found data file in installed package (via importlib)"
4. Change structured_logger.info( to structured_logger.debug(
5. Verify no other changes needed
```

## DATA
### Modified Log Entry
```python
# Log level change only - all other data unchanged
# Message: "Found data file in installed package (via importlib)"
# Level: info → debug
# Context data: method, path (unchanged)
```

### Impact on Workflow Output
- **INFO level**: Message will not appear (cleaner output)
- **DEBUG level**: Message will appear (detailed debugging)
- **All other functionality**: Completely unchanged

## LLM Prompt for Implementation

```
Based on the summary in pr_info/steps/summary.md, implement Step 3: Fix data files log level in src/mcp_coder/utils/data_files.py.

REQUIREMENTS:
1. Follow TDD - extend tests/utils/test_data_files.py with log level tests (NOTE: This is the only step with tests since data_files.py is core utility code)
2. Find the EXACT line with "Found data file in installed package (via importlib)" message
3. Change structured_logger.info( to structured_logger.debug( for this ONE line only
4. Do NOT modify any other logging statements
5. Do NOT change any function logic or return values

DELIVERABLES:
- Add 3 new test functions to tests/utils/test_data_files.py
- Change ONE log level in data_files.py from info to debug
- Verify the specific message only appears at DEBUG level

CONSTRAINTS:
- Change ONLY the log level of this specific message
- Do NOT modify any other parts of data_files.py
- Do NOT change the message text or context data
- Ensure all existing functionality works identically

VERIFICATION TARGET:
When running workflows/implement.py:
- Default (INFO): Should NOT show "Found data file in installed package (via importlib)"
- --log-level DEBUG: Should show the message with full debugging details

The goal is to match the example output provided where this message only appears in debug mode.
```

## Verification Steps  
1. Run `python workflows/implement.py` (INFO level) - should NOT see the data file message
2. Run `python workflows/implement.py --log-level DEBUG` - should see the data file message
3. Run tests: `pytest tests/utils/test_data_files.py::test_data_file_found_logs_debug_not_info -v`
4. Verify workflow still functions normally and finds data files correctly
5. Compare output to expected example in original requirements
