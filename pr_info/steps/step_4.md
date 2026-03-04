# Step 4: Implement Pattern-Based Log Matching

## Objective
Implement pattern-based log file matching in `_build_ci_error_details()` to fix the filename mismatch issue.

## Context
See `pr_info/steps/summary.md` for full context. This step implements the core fix - searching for logs using the actual GitHub filename pattern.

## WHERE
- **File**: `src/mcp_coder/checks/branch_status.py`
- **Function**: `_build_ci_error_details()` (lines ~430-500)
- **Specific location**: Inside the loop where logs are retrieved (around line 472-477)

## WHAT
Replace exact filename matching with pattern-based search:

### Current Code (line ~472-477)
```python
# Get log content for this job and strip timestamps
log_filename = f"{job_name}/{step_number}_{step_name}.txt"
log_content = logs.get(log_filename, "")
if log_content:
    log_content = _strip_timestamps(log_content)
```

### New Code
```python
# Get log content for this job using pattern matching
# GitHub format: {execution_number}_{job_name}.txt
log_content = ""
for filename, content in logs.items():
    if filename.endswith(f"_{job_name}.txt"):
        log_content = content
        break

# Fallback to old format if not found
if not log_content:
    log_filename = f"{job_name}/{step_number}_{step_name}.txt"
    log_content = logs.get(log_filename, "")

# Strip timestamps if content found
if log_content:
    log_content = _strip_timestamps(log_content)
```

## HOW
1. Locate the log retrieval section in `_build_ci_error_details()`
2. Find the loop: `for job in failed_jobs:`
3. Find where `log_filename` is constructed
4. Replace with pattern matching loop
5. Add fallback to old format
6. Keep timestamp stripping logic

## ALGORITHM
```
FOR each filename in logs dictionary:
    IF filename ends with "_{job_name}.txt":
        SET log_content = content
        BREAK loop
        
IF log_content is empty:
    TRY old format: "{job_name}/{step_number}_{step_name}.txt"
    
IF log_content found:
    STRIP timestamps
```

## DATA

### Input
- `logs`: Dict[str, str] - Mapping of filenames to log content
- `job_name`: str - Name of failed job (e.g., "file-size")

### Processing
```python
# Example logs dict from GitHub
logs = {
    "2_file-size.txt": "File size check failed...",
    "4_unit-tests.txt": "Test failures...",
    "9_vulture.txt": "Dead code found..."
}

# Pattern search for job_name = "file-size"
for filename, content in logs.items():
    if filename.endswith("_file-size.txt"):  # Matches "2_file-size.txt"
        log_content = content
        break
```

### Output
- `log_content`: str - Log content if found, empty string if not

## Integration Points
- No new imports needed
- Uses existing `logs` dict from `ci_manager.get_run_logs()`
- Uses existing `_strip_timestamps()` function
- Preserves all existing error handling

## Code Comments
Add explanatory comment:
```python
# Try pattern matching: GitHub format is {execution_number}_{job_name}.txt
# The execution number doesn't match step.number from API, so we pattern match
```

## Verification
```bash
# Run tests that should now PASS
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_single_failure -v
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_multiple_failures -v
pytest tests/checks/test_branch_status.py::test_collect_ci_status_with_truncation -v
```

Expected: These 3 tests now pass with log content displayed

## LLM Prompt
```
Review pr_info/steps/summary.md for context on issue #479.

Implement Step 4: Pattern-based log matching.

File: src/mcp_coder/checks/branch_status.py
Function: _build_ci_error_details() (around lines 472-477)

Replace the exact filename matching:
  log_filename = f"{job_name}/{step_number}_{step_name}.txt"
  log_content = logs.get(log_filename, "")

With pattern-based search (see step_4.md for complete code):
  1. Loop through logs.items()
  2. Match files ending with "_{job_name}.txt"
  3. Fallback to old format if not found
  4. Strip timestamps if content found

Add comment explaining GitHub's actual format vs expected format.

Run tests to verify:
- test_build_ci_error_details_single_failure
- test_build_ci_error_details_multiple_failures  
- test_collect_ci_status_with_truncation

All should PASS after this change.
```
