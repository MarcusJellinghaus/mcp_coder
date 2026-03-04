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
Replace exact filename matching with pattern-based search and update related warnings:

### Change 1: Pattern-Based Log Matching
**Current Code (line ~472-477)**
```python
# Get log content for this job and strip timestamps
log_filename = f"{job_name}/{step_number}_{step_name}.txt"
log_content = logs.get(log_filename, "")
if log_content:
    log_content = _strip_timestamps(log_content)
```

**New Code**
```python
# Get log content for this job using pattern matching
# GitHub format: {execution_number}_{job_name}.txt
# The execution number doesn't match step.number from API, so we pattern match
log_content = ""
matching_files = [f for f in logs.keys() if f.endswith(f"_{job_name}.txt")]

if matching_files:
    # Take first match
    log_content = logs[matching_files[0]]
    
    # Warn if multiple matches found (shouldn't happen normally)
    if len(matching_files) > 1:
        logger.warning(
            f"Multiple log files found for job '{job_name}': {matching_files}. "
            f"Using: {matching_files[0]}"
        )
else:
    # Fallback to old format if pattern match fails
    log_filename = f"{job_name}/{step_number}_{step_name}.txt"
    log_content = logs.get(log_filename, "")

# Strip timestamps if content found
if log_content:
    log_content = _strip_timestamps(log_content)
```

### Change 2: Update Warning in get_failed_jobs_summary()
**Location:** `get_failed_jobs_summary()` function (line ~305-310)

**Current Code**
```python
if not log_content and step_name:
    available_files = list(logs.keys())
    logger.warning(
        f"No log file found for failed step. Expected: '{log_filename}', "
        f"Available: {available_files}"
    )
```

**New Code**
```python
if not log_content and step_name:
    available_files = list(logs.keys())
    logger.warning(
        f"No log file found for job '{job_name}'. "
        f"Tried pattern: '*_{job_name}.txt', "
        f"Available: {available_files}"
    )
```

## HOW

### For _build_ci_error_details() (Change 1)
1. Locate the log retrieval section (line ~472-477)
2. Find the loop: `for job in failed_jobs:`
3. Find where `log_filename` is constructed
4. Replace with pattern matching using list comprehension
5. Add multi-match warning (Decision 1)
6. Add fallback to old format
7. Keep timestamp stripping logic

### For get_failed_jobs_summary() (Change 2)
1. Locate the warning message (line ~305-310)
2. Update warning text to reflect pattern matching
3. Change "Expected: '{log_filename}'" to "Tried pattern: '*_{job_name}.txt'"

## ALGORITHM

### Pattern Matching Logic
```
CREATE list of matching files where filename ends with "_{job_name}.txt"

IF matching_files is not empty:
    SET log_content = logs[matching_files[0]]
    
    IF len(matching_files) > 1:
        LOG warning with all matching filenames
        
ELSE (no pattern match):
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
Comments are included in the new code above:
- Explains GitHub's actual format
- Notes the mismatch between execution number and step number
- Documents the multi-match warning behavior

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
Review pr_info/steps/summary.md and decisions.md for context on issue #479.

Implement Step 4: Pattern-based log matching with warnings.

Make TWO changes:

**Change 1: _build_ci_error_details() function (line ~472-477)**
File: src/mcp_coder/checks/branch_status.py

Replace exact filename matching with pattern-based search:
  1. Use list comprehension to find matching files: [f for f in logs.keys() if f.endswith(f"_{job_name}.txt")]
  2. Take first match if found
  3. Add warning if multiple matches found (Decision 1)
  4. Fallback to old format if no match
  5. Strip timestamps if content found

See step_4.md for complete code.

**Change 2: get_failed_jobs_summary() function (line ~305-310)**
File: src/mcp_coder/checks/branch_status.py

Update warning message:
  - Change from: "Expected: '{log_filename}'"
  - To: "Tried pattern: '*_{job_name}.txt'"

This reflects the new pattern-matching approach (Decision 4).

Run tests to verify:
- test_build_ci_error_details_single_failure
- test_build_ci_error_details_multiple_failures  
- test_collect_ci_status_with_truncation
- test_build_ci_error_details_fallback_to_old_format (NEW - should now PASS)

All should PASS after these changes.
```
