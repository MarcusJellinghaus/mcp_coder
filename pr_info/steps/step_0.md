# Step 0: Enhance CIResultsManager with Step-Level Data

## Overview

Enhance `CIResultsManager.get_latest_ci_status()` to include step-level information for each job. This enables precise identification of which step failed and construction of the correct log filename.

## LLM Prompt for This Step

```
Implement Step 0 from pr_info/steps/step_0.md.

Reference the summary at pr_info/steps/summary.md for context.

This step enhances CIResultsManager to include step-level data for each job.
Follow TDD: write tests first, then implement.
```

---

## Part 1: Write Tests First

### WHERE
`tests/utils/github_operations/test_ci_results_manager_status.py` (append to existing tests)

### WHAT
Add tests for step-level data in job info:

```python
class TestGetLatestCIStatusSteps:
    """Tests for step-level data in get_latest_ci_status."""

    def test_jobs_include_steps_data(self):
        """Job info should include steps array with number, name, conclusion."""
        # Setup mock with job steps
        # Verify steps data is included in response

    def test_steps_contain_required_fields(self):
        """Each step should have number, name, and conclusion fields."""
        # Verify step structure

    def test_empty_steps_when_job_has_no_steps(self):
        """Jobs with no steps should have empty steps array."""
        # Handle edge case
```

### HOW
Append to existing test file, using existing mock patterns.

---

## Part 2: Update CIStatusData TypedDict

### WHERE
`src/mcp_coder/utils/github_operations/ci_results_manager.py`

### WHAT
Update the jobs type hint to include steps:

```python
class CIStatusData(TypedDict):
    """TypedDict for CI status data structure."""

    run: Dict[str, Any]
    jobs: List[Dict[str, Any]]  # Now includes 'steps' key
```

Add docstring note:
```python
# jobs structure:
# [{id, name, status, conclusion, started_at, completed_at,
#   steps: [{number, name, conclusion}]}]
```

---

## Part 3: Update get_latest_ci_status Implementation

### WHERE
`src/mcp_coder/utils/github_operations/ci_results_manager.py`

### WHAT
Modify the job data transformation to include steps:

```python
# In get_latest_ci_status(), update job_data dict:
job_data = {
    "id": job.id,
    "name": job.name,
    "status": job.status,
    "conclusion": job.conclusion,
    "started_at": job.started_at.isoformat() if job.started_at else None,
    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    "steps": [
        {
            "number": step.number,
            "name": step.name,
            "conclusion": step.conclusion,
        }
        for step in job.steps
    ],
}
```

### ALGORITHM
```
1. In the jobs loop, after creating job_data dict
2. Access job.steps (PyGithub provides this)
3. Transform each step to dict with number, name, conclusion
4. Add steps list to job_data
```

### DATA

**Step structure:**
```python
{
    "number": int,      # Step number (1, 2, 3, ...)
    "name": str,        # Step name ("Set up job", "Run tests", etc.)
    "conclusion": str,  # "success", "failure", "skipped", None
}
```

---

## Verification

1. Run tests: `pytest tests/utils/github_operations/test_ci_results_manager_status.py -v`
2. All tests should pass
3. Verify step data is correctly extracted from GitHub API
