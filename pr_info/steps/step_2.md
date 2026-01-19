# Step 2: Add Helper Functions with Tests (TDD)

## Overview

Implement two helper functions for CI log processing. Follow TDD: write tests first, then implement.

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


class TestExtractLogExcerpt:
    """Tests for _extract_log_excerpt function."""

    def test_short_log_returned_unchanged(self):
        """Logs under 200 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(100)])
        from mcp_coder.workflows.implement.core import _extract_log_excerpt
        
        result = _extract_log_excerpt(log)
        
        assert result == log

    def test_exactly_200_lines_returned_unchanged(self):
        """Logs of exactly 200 lines should be returned as-is."""
        log = "\n".join([f"Line {i}" for i in range(200)])
        from mcp_coder.workflows.implement.core import _extract_log_excerpt
        
        result = _extract_log_excerpt(log)
        
        assert result == log

    def test_long_log_truncated_to_first_30_last_170(self):
        """Logs over 200 lines should have first 30 + last 170 lines."""
        log = "\n".join([f"Line {i}" for i in range(300)])
        from mcp_coder.workflows.implement.core import _extract_log_excerpt
        
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
        from mcp_coder.workflows.implement.core import _extract_log_excerpt
        
        result = _extract_log_excerpt("")
        
        assert result == ""


class TestGetFailedJobsSummary:
    """Tests for _get_failed_jobs_summary function."""

    def test_single_failed_job_returns_details(self):
        """Single failed job should return its name and log."""
        jobs = [
            {"name": "build", "conclusion": "success"},
            {"name": "test", "conclusion": "failure"},
        ]
        logs = {"test/1_Run tests.txt": "Error: test failed\nAssertionError"}
        from mcp_coder.workflows.implement.core import _get_failed_jobs_summary
        
        job_name, log_excerpt, other_jobs = _get_failed_jobs_summary(jobs, logs)
        
        assert job_name == "test"
        assert "Error: test failed" in log_excerpt
        assert other_jobs == []

    def test_multiple_failed_jobs_returns_first_with_others_listed(self):
        """Multiple failed jobs should detail first, list others."""
        jobs = [
            {"name": "lint", "conclusion": "failure"},
            {"name": "test", "conclusion": "failure"},
            {"name": "build", "conclusion": "failure"},
        ]
        logs = {
            "lint/1_Run lint.txt": "Lint error",
            "test/1_Run tests.txt": "Test error",
            "build/1_Build.txt": "Build error",
        }
        from mcp_coder.workflows.implement.core import _get_failed_jobs_summary
        
        job_name, log_excerpt, other_jobs = _get_failed_jobs_summary(jobs, logs)
        
        assert job_name == "lint"  # First failed job
        assert "Lint error" in log_excerpt
        assert "test" in other_jobs
        assert "build" in other_jobs
        assert len(other_jobs) == 2

    def test_no_failed_jobs_returns_empty(self):
        """No failed jobs should return empty values."""
        jobs = [
            {"name": "build", "conclusion": "success"},
            {"name": "test", "conclusion": "success"},
        ]
        logs = {}
        from mcp_coder.workflows.implement.core import _get_failed_jobs_summary
        
        job_name, log_excerpt, other_jobs = _get_failed_jobs_summary(jobs, logs)
        
        assert job_name == ""
        assert log_excerpt == ""
        assert other_jobs == []

    def test_failed_job_with_no_matching_log(self):
        """Failed job without matching log should return job name but empty excerpt."""
        jobs = [{"name": "test", "conclusion": "failure"}]
        logs = {}  # No logs available
        from mcp_coder.workflows.implement.core import _get_failed_jobs_summary
        
        job_name, log_excerpt, other_jobs = _get_failed_jobs_summary(jobs, logs)
        
        assert job_name == "test"
        assert log_excerpt == ""
        assert other_jobs == []
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
) -> tuple[str, str, list[str]]:
    """Get summary of failed jobs from CI status.
    
    Args:
        jobs: List of job dicts with 'name' and 'conclusion' keys
        logs: Dict mapping log filenames to content
    
    Returns:
        Tuple of (first_failed_job_name, log_excerpt, other_failed_job_names)
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
2. If no failed jobs: return ("", "", [])
3. First failed job = failed_jobs[0]["name"]
4. Find matching log (job name appears in log filename)
5. Extract log excerpt using _extract_log_excerpt
6. Other failed jobs = [j["name"] for j in failed_jobs[1:]]
7. Return (first_job_name, excerpt, other_jobs)
```

### DATA

**_extract_log_excerpt:**
- Input: `str` (log content)
- Output: `str` (possibly truncated log)

**_get_failed_jobs_summary:**
- Input: `list[dict]` (jobs from CIStatusData), `dict[str, str]` (logs)
- Output: `tuple[str, str, list[str]]` (job_name, log_excerpt, other_job_names)

---

## Verification

1. Run tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. All tests should pass
3. Functions should handle edge cases (empty input, no failures, etc.)
