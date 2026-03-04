# Step 6: Enhance Error Message When Logs Unavailable

## Objective
Improve the "(logs not available)" message to include GitHub URL for user navigation when logs can't be found locally.

## Context
See `pr_info/steps/summary.md` for full context. This step enhances the error message to be more helpful by directing users to GitHub.

## WHERE
- **File**: `src/mcp_coder/checks/branch_status.py`
- **Function**: `_build_ci_error_details()` (lines ~430-500)
- **Specific location**: In the job loop where log content is displayed (around line 495)

## WHAT
Replace simple error message with URL-enhanced version:

### Current Code (line ~495)
```python
output_lines.append(log_content if log_content else "(logs not available)")
```

### New Code
```python
# Display log content or helpful error message
if log_content:
    output_lines.append(log_content)
else:
    # Provide GitHub URL if logs not available locally
    job_id = job.get("id")
    if run_url and job_id:
        error_msg = f"(logs not available locally)\nView on GitHub: {run_url}/job/{job_id}"
    else:
        error_msg = "(logs not available)"
    output_lines.append(error_msg)
```

## HOW
1. Locate where log content is appended to output_lines
2. Replace ternary operator with if/else block
3. Add URL to error message when available
4. Keep fallback to simple message

## ALGORITHM
```
IF log_content exists:
    APPEND log_content to output
ELSE:
    IF run_url and job_id exist:
        CREATE message with GitHub URL
    ELSE:
        USE simple "(logs not available)" message
    APPEND error message to output
```

## DATA

### Input
- `log_content`: str - Empty string if logs not found
- `run_url`: str - GitHub Actions run URL
- `job_id`: int - Job identifier from job dict

### Output Examples

**Case 1: URL available**
```
## Job: file-size
View job: https://github.com/user/repo/actions/runs/12345/job/67890
Failed step: Run file-size

(logs not available locally)
View on GitHub: https://github.com/user/repo/actions/runs/12345/job/67890
```

**Case 2: URL not available**
```
## Job: file-size
Failed step: Run file-size

(logs not available)
```

## Integration Points
- Uses existing `log_content` variable
- Uses `run_url` from Step 5
- Uses `job_id` already extracted in job loop
- No new imports needed

## Code Comments
Add explanatory comment:
```python
# Provide GitHub URL if logs not available locally (helps user navigate to logs)
```

## Verification
```bash
# Run new test that should now PASS
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_logs_not_available_with_url -v

# Also verify existing functionality still works
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_single_failure -v
```

Expected: Both tests pass

## Notes
- The `job_id` is already extracted earlier in Step 5, so just reuse it
- Multi-line error message improves readability
- Graceful fallback ensures robustness

## LLM Prompt
```
Review pr_info/steps/summary.md for context on issue #479.

Implement Step 6: Enhance error message when logs unavailable.

File: src/mcp_coder/checks/branch_status.py
Function: _build_ci_error_details()

Find the line (around 495):
  output_lines.append(log_content if log_content else "(logs not available)")

Replace with if/else block (see step_6.md for complete code):
  IF log_content:
      Append log_content
  ELSE:
      Create error message with GitHub URL if available
      Fallback to simple message otherwise

Add explanatory comment about helping user navigate to logs.

Run tests to verify:
- test_build_ci_error_details_logs_not_available_with_url
- test_build_ci_error_details_single_failure

Both should PASS after this change.
```
