# Step 1: Models and Model Tests (TDD)

## LLM Prompt

```
You are implementing Step 1 of the Jenkins Job Automation feature for the mcp_coder project.

Read the following files to understand the context:
1. pr_info/steps/summary.md - Overall implementation summary
2. This step file (pr_info/steps/step_1.md) - Current step details

Your task:
- Follow Test-Driven Development (TDD)
- Create model tests FIRST, then implement models to pass tests
- Use MCP filesystem tools (mcp__filesystem__save_file) for all file operations
- Follow existing patterns from src/mcp_coder/utils/git_operations/core.py (CommitResult, PushResult)
- Ensure all code follows KISS principle and project conventions
- After implementation, run: mcp__code-checker__run_pytest_check with the new test file

Important:
- Use @dataclass decorator from dataclasses
- Implement __str__() methods for human-readable output
- Full type hints with Optional types
- Clear docstrings with examples
```

---

## Objective
Create data models for Jenkins operations and their comprehensive tests following TDD approach.

---

## WHERE: File Paths

### Test File (Create FIRST):
```
tests/utils/jenkins_operations/test_models.py
```

### Source File (Create SECOND):
```
src/mcp_coder/utils/jenkins_operations/models.py
```

### Directory Setup:
Create directories if they don't exist:
- `src/mcp_coder/utils/jenkins_operations/`
- `tests/utils/jenkins_operations/`

---

## WHAT: Main Components

### 1. JobStatus Dataclass

**Signature:**
```python
@dataclass
class JobStatus:
    """Represents the status of a Jenkins job."""
    status: str
    build_number: Optional[int]
    duration_ms: Optional[int]
    url: Optional[str]
    
    def __str__(self) -> str:
        """Return human-readable job status."""
```

**Purpose:** Hold job execution status information returned from Jenkins API.

**Fields:**
- `status`: Job state - "queued", "running", "SUCCESS", "FAILURE", "ABORTED", "UNSTABLE"
- `build_number`: Build number once job starts (None if still queued)
- `duration_ms`: Duration in milliseconds (None if not completed)
- `url`: Jenkins job URL (None if not available)

### 2. QueueSummary Dataclass

**Signature:**
```python
@dataclass
class QueueSummary:
    """Summary of Jenkins queue status."""
    running: int
    queued: int
    
    def __str__(self) -> str:
        """Return human-readable queue summary."""
```

**Purpose:** Hold Jenkins queue statistics.

**Fields:**
- `running`: Number of jobs currently running
- `queued`: Number of jobs waiting in queue

---

## HOW: Integration Points

### Imports Required:

**For models.py:**
```python
from dataclasses import dataclass
from typing import Optional
```

**For test_models.py:**
```python
import pytest
from mcp_coder.utils.jenkins_operations.models import JobStatus, QueueSummary
```

### Decorators:
- `@dataclass` - Makes class a dataclass with auto-generated __init__, __repr__, __eq__

### Pattern References:
- Follow: `src/mcp_coder/utils/git_operations/core.py` (CommitResult, PushResult dataclasses)

---

## ALGORITHM: Core Logic

### JobStatus.__str__() Algorithm:
```python
1. If status is "queued":
   return "Job queued"
2. If build_number exists:
   format = f"Job #{build_number}: {status}"
   if duration_ms exists:
       format += f" ({duration_ms}ms)"
   return format
3. Otherwise:
   return status
```

### QueueSummary.__str__() Algorithm:
```python
1. Create running_text = f"{running} job{'s' if running != 1 else ''} running"
2. Create queued_text = f"{queued} job{'s' if queued != 1 else ''} queued"
3. Return f"{running_text}, {queued_text}"
```

---

## DATA: Return Values and Structures

### JobStatus Examples:

```python
# Queued job
JobStatus(status="queued", build_number=None, duration_ms=None, url=None)
# str: "Job queued"

# Running job
JobStatus(status="running", build_number=42, duration_ms=None, 
          url="https://jenkins.example.com/job/test/42")
# str: "Job #42: running"

# Completed job
JobStatus(status="SUCCESS", build_number=42, duration_ms=1234, 
          url="https://jenkins.example.com/job/test/42")
# str: "Job #42: SUCCESS (1234ms)"
```

### QueueSummary Examples:

```python
# Multiple jobs
QueueSummary(running=3, queued=2)
# str: "3 jobs running, 2 jobs queued"

# Single job
QueueSummary(running=1, queued=0)
# str: "1 job running, 0 jobs queued"

# Empty queue
QueueSummary(running=0, queued=0)
# str: "0 jobs running, 0 jobs queued"
```

---

## Test Implementation (CREATE FIRST)

### File: tests/utils/jenkins_operations/test_models.py

**Required Tests:**

1. **test_job_status_creation**
   - Create JobStatus with all fields
   - Verify all fields are set correctly
   - Test Optional fields with None values

2. **test_job_status_str_queued**
   - Create queued job (build_number=None)
   - Verify __str__() returns "Job queued"

3. **test_job_status_str_running**
   - Create running job (build_number set, duration_ms=None)
   - Verify __str__() returns "Job #42: running"

4. **test_job_status_str_completed**
   - Create completed job (all fields set)
   - Verify __str__() returns "Job #42: SUCCESS (1234ms)"

5. **test_queue_summary_creation**
   - Create QueueSummary with counts
   - Verify fields are set correctly

6. **test_queue_summary_str_multiple**
   - Create summary with multiple jobs
   - Verify __str__() returns "3 jobs running, 2 jobs queued"

7. **test_queue_summary_str_singular**
   - Create summary with single job
   - Verify __str__() returns "1 job running, 0 jobs queued"

8. **test_queue_summary_str_empty**
   - Create summary with zero jobs
   - Verify __str__() returns "0 jobs running, 0 jobs queued"

**Test Structure:**
```python
"""Tests for Jenkins operation models."""

import pytest

from mcp_coder.utils.jenkins_operations.models import JobStatus, QueueSummary


class TestJobStatus:
    """Tests for JobStatus dataclass."""
    
    def test_job_status_creation(self) -> None:
        """Test JobStatus creation with all fields."""
        # Test implementation
        
    # ... more tests


class TestQueueSummary:
    """Tests for QueueSummary dataclass."""
    
    def test_queue_summary_creation(self) -> None:
        """Test QueueSummary creation."""
        # Test implementation
        
    # ... more tests
```

---

## Source Implementation (CREATE SECOND)

### File: src/mcp_coder/utils/jenkins_operations/models.py

**Module Docstring:**
```python
"""Data models for Jenkins job operations.

This module provides dataclasses for representing Jenkins job status
and queue information.

Example:
    >>> status = JobStatus(status="SUCCESS", build_number=42, 
    ...                    duration_ms=1234, url="https://jenkins.example.com/job/test/42")
    >>> print(status)
    Job #42: SUCCESS (1234ms)
    
    >>> summary = QueueSummary(running=3, queued=2)
    >>> print(summary)
    3 jobs running, 2 jobs queued
"""
```

**Implementation:**
1. Import required modules (dataclasses, typing)
2. Define JobStatus dataclass with fields and __str__()
3. Define QueueSummary dataclass with fields and __str__()

**Key Requirements:**
- Use `@dataclass` decorator
- All fields with type hints
- Optional fields use `Optional[type]`
- Implement __str__() for human-readable output
- Include comprehensive docstrings with examples

---

## Validation Steps

After implementation, verify:

1. **Create __init__.py files:**
   ```python
   # tests/utils/jenkins_operations/__init__.py
   """Tests for Jenkins operations."""
   
   # src/mcp_coder/utils/jenkins_operations/__init__.py  
   """Jenkins job automation utilities."""
   # (Will be populated in Step 4)
   ```

2. **Run tests:**
   ```python
   # Use MCP tool to run specific test file
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-v", "tests/utils/jenkins_operations/test_models.py"]
   )
   ```

3. **Verify output:**
   - All tests should pass
   - No import errors
   - No type errors

4. **Run mypy:**
   ```python
   mcp__code-checker__run_mypy_check(
       target_directories=["src/mcp_coder/utils/jenkins_operations"]
   )
   ```

---

## Expected Outcomes

✅ **Files created:**
- `tests/utils/jenkins_operations/__init__.py` (empty with docstring)
- `tests/utils/jenkins_operations/test_models.py` (~80-100 lines)
- `src/mcp_coder/utils/jenkins_operations/__init__.py` (placeholder)
- `src/mcp_coder/utils/jenkins_operations/models.py` (~60-80 lines)

✅ **All tests pass** (8 tests total)

✅ **Type checking passes** (mypy clean)

✅ **Models are:**
- Immutable (dataclass default)
- Type-safe (full type hints)
- Human-readable (__str__ methods)
- Well-documented (docstrings with examples)

---

## Next Step

After Step 1 is complete and all tests pass, proceed to:
- **Step 2:** Client implementation with unit tests (TDD)
