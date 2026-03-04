# Step 5: Add GitHub URL Display

## Objective
Add GitHub Actions URLs to the error output for easy navigation to the actual CI runs.

## Context
See `pr_info/steps/summary.md` for full context. This step adds run URL at the top and job URLs for each failed job.

## WHERE
- **File**: `src/mcp_coder/checks/branch_status.py`
- **Function**: `_build_ci_error_details()` (lines ~430-500)
- **Two locations**:
  1. Top of output - after summary placeholder (line ~455)
  2. Job section - after job name (line ~485)

## WHAT
Add URL extraction and display in two places:

### Location 1: Run URL at Top
**After line ~442** (before building output_lines):
```python
# Extract GitHub Actions run URL
run_url = run_data.get("url", "")
```

**After line ~456** (after summary_placeholder_idx):
```python
# Section 1: Summary header (will be updated at end)
summary_placeholder_idx = len(output_lines)
output_lines.append("")  # Placeholder for summary
output_lines.append("")
lines_used += 2

# Add GitHub Actions run URL if available
if run_url:
    output_lines.append(f"GitHub Actions: {run_url}")
    output_lines.append("")
    lines_used += 2
```

### Location 2: Job URL in Each Job Section
**After line ~485** (after "## Job: {job_name}"):
```python
# Add job section
output_lines.append(f"## Job: {job_name}")

# Add job URL if available
job_id = job.get("id")
if run_url and job_id:
    output_lines.append(f"View job: {run_url}/job/{job_id}")
    
output_lines.append(f"Failed step: {step_name}")
```

## HOW
1. Extract `run_url` from `run_data` at start of function
2. Add URL display after summary section
3. Extract `job_id` from each job dict
4. Add job URL after job header

## ALGORITHM
```
EXTRACT run_url from run_data
IF run_url exists:
    ADD "GitHub Actions: {run_url}" to output

FOR each failed job:
    EXTRACT job_id from job dict
    ADD "## Job: {job_name}"
    IF run_url and job_id exist:
        ADD "View job: {run_url}/job/{job_id}"
    ADD "Failed step: {step_name}"
```

## DATA

### Input
```python
run_data = {
    "id": 12345,
    "url": "https://github.com/user/repo/actions/runs/12345",
    "conclusion": "failure"
}

job = {
    "id": 67890,
    "name": "file-size",
    "conclusion": "failure",
    "steps": [...]
}
```

### Output Format
```
## CI Failure Summary
Failed jobs (1): file-size

GitHub Actions: https://github.com/user/repo/actions/runs/12345

## Job: file-size
View job: https://github.com/user/repo/actions/runs/12345/job/67890
Failed step: Run file-size

(log content here)
```

## Integration Points
- Uses existing `run_data` parameter
- Uses existing `job` dict from loop
- No new imports needed
- Integrates with existing output_lines list

## Code Comments
Add explanatory comments:
```python
# Extract GitHub Actions run URL for user navigation
run_url = run_data.get("url", "")
```

```python
# Add job URL if available (helps user navigate to specific job)
job_id = job.get("id")
if run_url and job_id:
    output_lines.append(f"View job: {run_url}/job/{job_id}")
```

## Verification
```bash
# Run new test that should now PASS
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_includes_github_urls -v
```

Expected: Test passes with URLs displayed correctly

## LLM Prompt
```
Review pr_info/steps/summary.md for context on issue #479.

Implement Step 5: Add GitHub URL display.

File: src/mcp_coder/checks/branch_status.py
Function: _build_ci_error_details()

Make two changes:

1. At top of function (after line ~442):
   Extract: run_url = run_data.get("url", "")

2. After summary placeholder section (after line ~456):
   Add GitHub Actions run URL display (see step_5.md for code)

3. In job loop, after "## Job: {job_name}" (around line ~485):
   Add job URL display using job.get("id") (see step_5.md for code)

Add explanatory comments for each URL section.

Run test to verify:
- test_build_ci_error_details_includes_github_urls

Should PASS after this change.
```
