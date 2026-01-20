# Step 2: Add Helper Functions with Tests (TDD)

## Overview

Implement two helper functions for CI log processing. Follow TDD: write tests first, then implement.

**Prerequisites:** Step 0 must be complete (CIResultsManager has step-level data).

## LLM Prompt for This Step

```
Implement Step 2 from pr_info/steps/step_2.md.

Reference the summary at pr_info/steps/summary.md for context.

This step adds helper functions for CI log processing using TDD approach.
Write tests first, then implement the functions.
```

---

## Part 1: Write Tests First

### WHERE
`tests/workflows/implement/test_ci_check.py` (new file)

### WHAT
Create test file with tests for helper functions:

```python
"""Tests for CI check helper functions."""

import pytest

from mcp_coder.workflows.implement.core import (
    _extract_log_excerpt,
    _get_failed_jobs_summary,
)


class TestExtractLogExcerpt:
    """Tests for _extract_log_excerpt function."""

    def test_short_log_returned_unchanged(self):
        """Logs under 200 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(100)])
        
        result = _extract_log_excerpt(log)
        
        assert result == log

    def test_exactly_200_lines_returned_unchanged(self):
        """Logs of exactly 200 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(200)])
        
        result = _extract_log_excerpt(log)
        
        assert result == log

    def test_long_log_truncated_to_first_30_last_170(self):
        """Logs over 200 lines should have first 30 + last 170 lines."""
        log = "\n".join([f"Line {i}" for i in range(300)])
        
        result = _extract_log_excerpt(log)
        lines = result.split("\n")
        
        # Should have 200 lines + truncation marker
        assert "Line 0" in result  # First line preserved
        assert "Line 29" in result  # Line 30 preserved (0-indexed)
        assert "Line 299" in result  # Last line preserved
        assert "Line 130" in result  # From last 170 (300-170=130)
        assert "Line 30" not in result  # Should be truncated
        assert "Line 129" not in result  # Should be truncated
        assert "..." in result or "[truncated]" in result.lower()

    def test_empty_log_returns_empty(self):
        """Empty log should return empty string."""
        result = _extract_log_excerpt("")
        
        assert result == ""


class TestGetFailedJobsSummary:
    """Tests for _get_failed_jobs_summary function."""

    def test_single_failed_job_returns_details_with_step_info(self):
        """Single failed job should return its name, step info, and log."""
        jobs = [
            {"name": "build", "conclusion": "success", "steps": []},
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"number": 1, "name": "Set up job", "conclusion": "success"},
                    {"number": 2, "name": "Checkout", "conclusion": "success"},
                    {"number": 3, "name": "Run tests", "conclusion": "failure"},
                ],
            },
        ]
        logs = {"test/3_Run tests.txt": "Error: test failed\nAssertionError"}
        
        result = _get_failed_jobs_summary(jobs, logs)
        
        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["step_number"] == 3
        assert "Error: test failed" in result["log_excerpt"]
        assert result["other_failed_jobs"] == []

    def test_multiple_failed_jobs_returns_first_with_others_listed(self):
        """Multiple failed jobs should detail first, list others."""
        jobs = [
            {
                "name": "lint",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run lint", "conclusion": "failure"}],
            },
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
            },
            {
                "name": "build",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Build", "conclusion": "failure"}],
            },
        ]
        logs = {
            "lint/1_Run lint.txt": "Lint error",
            "test/1_Run tests.txt": "Test error",
            "build/1_Build.txt": "Build error",
        }
        
        result = _get_failed_jobs_summary(jobs, logs)
        
        assert result["job_name"] == "lint"  # First failed job
        assert "Lint error" in result["log_excerpt"]
        assert "test" in result["other_failed_jobs"]
        assert "build" in result["other_failed_jobs"]
        assert len(result["other_failed_jobs"]) == 2

    def test_no_failed_jobs_returns_empty(self):
        """No failed jobs should return empty values."""
        jobs = [
            {"name": "build", "conclusion": "success", "steps": []},
            {"name": "test", "conclusion": "success", "steps": []},
        ]
        logs = {}
        
        result = _get_failed_jobs_summary(jobs, logs)
        
        assert result["job_name"] == ""
        assert result["step_name"] == ""
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_failed_job_with_no_matching_log(self):
        """Failed job without matching log should return job/step info but empty excerpt."""
        jobs = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
            }
        ]
        logs = {}  # No logs available
        
        result = _get_failed_jobs_summary(jobs, logs)
        
        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_constructs_correct_log_filename(self):
        """Should construct log filename from job name, step number, and step name.
        
        Note: Uses exact filename matching only (Decision 10). If no match found,
        log_excerpt will be empty.
        """
        jobs = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"number": 1, "name": "Set up job", "conclusion": "success"},
                    {"number": 2, "name": "Run tests", "conclusion": "failure"},
                ],
            }
        ]
        # Log filename format: {job_name}/{step_number}_{step_name}.txt
        logs = {"test/2_Run tests.txt": "Test failure output"}
        
        result = _get_failed_jobs_summary(jobs, logs)
        
        assert "Test failure output" in result["log_excerpt"]
```

### HOW
Create new test file in existing test directory structure.

---

## Part 2: Implement Helper Functions

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Add two helper functions near the top of the file (after imports, before existing functions):

```python
def _extract_log_excerpt(log: str, max_lines: int = 200) -> str:
    """Extract log excerpt: first 30 + last 170 lines if log exceeds max_lines.
    
    Args:
        log: Full log content as string
        max_lines: Maximum lines before truncation (default 200)
    
    Returns:
        Original log if under max_lines, otherwise truncated with marker
    """
    pass  # Implement based on tests


def _get_failed_jobs_summary(
    jobs: list[dict], logs: dict[str, str]
) -> dict[str, Any]:
    """Get summary of failed jobs from CI status.
    
    Args:
        jobs: List of job dicts with 'name', 'conclusion', and 'steps' keys
        logs: Dict mapping log filenames to content
    
    Returns:
        Dict with keys: job_name, step_name, step_number, log_excerpt, other_failed_jobs
    """
    pass  # Implement based on tests
```

### ALGORITHM for _extract_log_excerpt
```
1. Split log into lines
2. If len(lines) <= max_lines: return original log
3. Take first 30 lines
4. Add truncation marker "[... truncated {N} lines ...]"
5. Take last 170 lines
6. Join and return
```

### ALGORITHM for _get_failed_jobs_summary
```
1. Filter jobs where conclusion == "failure"
2. If no failed jobs: return empty result dict
3. First failed job = failed_jobs[0]
4. Find first step with conclusion == "failure" in job["steps"]
5. Construct log filename: f"{job_name}/{step_number}_{step_name}.txt"
6. Look up log content from logs dict
7. Extract log excerpt using _extract_log_excerpt
8. Other failed jobs = [j["name"] for j in failed_jobs[1:]]
9. Return result dict
```

### DATA

**_extract_log_excerpt:**
- Input: `str` (log content)
- Output: `str` (possibly truncated log)

**_get_failed_jobs_summary:**
- Input: `list[dict]` (jobs from CIStatusData with steps), `dict[str, str]` (logs)
- Output: `dict` with structure:
  ```python
  {
      "job_name": str,
      "step_name": str,
      "step_number": int,
      "log_excerpt": str,
      "other_failed_jobs": list[str],
  }
  ```

---

## Verification

1. Run tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. All tests should pass
3. Functions should handle edge cases (empty input, no failures, etc.)
