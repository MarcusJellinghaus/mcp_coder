# Step 4: Module Exports and Public API

## LLM Prompt

```
You are implementing Step 4 of the Jenkins Job Automation feature for the mcp_coder project.

Read the following files to understand the context:
1. pr_info/steps/summary.md - Overall implementation summary
2. pr_info/steps/step_1.md - Models implementation
3. pr_info/steps/step_2.md - Client implementation
4. pr_info/steps/step_3.md - Integration tests
5. This step file (pr_info/steps/step_4.md) - Current step details

Your task:
- Create jenkins_operations/__init__.py to export public API
- Update utils/__init__.py to include jenkins_operations exports
- Follow existing patterns from git_operations and github_operations
- Use MCP filesystem tools (mcp__filesystem__save_file, mcp__filesystem__edit_file)
- Verify imports work by running a quick import test

Important:
- Only export public API (classes, dataclasses, exceptions)
- Don't export private helpers (like _get_jenkins_config)
- Keep __all__ list organized alphabetically by category
- Follow existing export patterns in utils/__init__.py
```

---

## Objective
Set up module exports to make jenkins_operations accessible via `from mcp_coder.utils import JenkinsClient`.

---

## WHERE: File Paths

### Create:
```
src/mcp_coder/utils/jenkins_operations/__init__.py
```

### Modify:
```
src/mcp_coder/utils/__init__.py
```

---

## WHAT: Main Components

### 1. Jenkins Operations Package Exports

**Purpose:** Define public API for jenkins_operations module.

**Exports:**
- `JenkinsClient` - Main client class
- `JobStatus` - Job status dataclass
- `QueueSummary` - Queue summary dataclass
- `JenkinsError` - Base exception
- `JenkinsConnectionError` - Connection error
- `JenkinsAuthError` - Authentication error
- `JenkinsJobNotFoundError` - Job not found error

**DO NOT Export:**
- `_get_jenkins_config()` - Private helper function

### 2. Utils Package Exports

**Purpose:** Make jenkins_operations accessible from utils package.

**Add to existing exports:**
- All jenkins_operations public exports listed above

---

## HOW: Integration Points

### Pattern References:

**Similar Patterns:**
- `src/mcp_coder/utils/git_operations/__init__.py` - Organized exports with __all__
- `src/mcp_coder/utils/github_operations/__init__.py` - Manager class exports
- `src/mcp_coder/utils/__init__.py` - Top-level utils exports

**Export Style:**
```python
# Import from submodules
from .client import (
    JenkinsClient,
    JenkinsError,
    # ...
)
from .models import JobStatus, QueueSummary

# Define __all__ for explicit exports
__all__ = [
    # Client
    "JenkinsClient",
    # Models
    "JobStatus",
    "QueueSummary",
    # Exceptions
    "JenkinsError",
    # ...
]
```

---

## ALGORITHM: Implementation Steps

### Step 4.1: Create jenkins_operations/__init__.py
```
1. Add module docstring explaining the package
2. Import public classes from .client (JenkinsClient, exceptions)
3. Import dataclasses from .models (JobStatus, QueueSummary)
4. Define __all__ list with all public exports
5. Organize __all__ by category (client, models, exceptions)
```

### Step 4.2: Update utils/__init__.py
```
1. Read current file to understand structure
2. Add import statement for jenkins_operations
3. Add jenkins_operations exports to __all__ list
4. Maintain alphabetical organization within categories
5. Keep existing comment structure
```

---

## DATA: File Contents

### src/mcp_coder/utils/jenkins_operations/__init__.py

**Complete file content:**

```python
"""Jenkins job automation utilities.

This package provides utilities for interacting with Jenkins servers
to start jobs, check status, and monitor the queue.

Main Components:
    JenkinsClient: Main client for Jenkins operations
    JobStatus: Dataclass for job status information
    QueueSummary: Dataclass for queue statistics
    
Custom Exceptions:
    JenkinsError: Base exception for Jenkins operations
    JenkinsConnectionError: Connection failed
    JenkinsAuthError: Authentication failed
    JenkinsJobNotFoundError: Job not found

Example:
    >>> from mcp_coder.utils import JenkinsClient, JobStatus
    >>> client = JenkinsClient("http://jenkins:8080", "user", "token")
    >>> queue_id = client.start_job("my-job", {"PARAM": "value"})
    >>> status = client.get_job_status(queue_id)
    >>> print(status)
    Job #42: running
    
Configuration:
    See client.py for configuration details.
"""

# Client and exceptions
from .client import (
    JenkinsAuthError,
    JenkinsClient,
    JenkinsConnectionError,
    JenkinsError,
    JenkinsJobNotFoundError,
)

# Data models
from .models import JobStatus, QueueSummary

__all__ = [
    # Client
    "JenkinsClient",
    # Models
    "JobStatus",
    "QueueSummary",
    # Exceptions
    "JenkinsAuthError",
    "JenkinsConnectionError",
    "JenkinsError",
    "JenkinsJobNotFoundError",
]
```

**File characteristics:**
- ~60 lines
- Clear module docstring with example
- Organized imports (client, then models)
- __all__ list organized by category
- Alphabetical within categories

---

## Source Implementation

### File 1: Create jenkins_operations/__init__.py

**Use MCP tool:**
```python
mcp__filesystem__save_file(
    file_path="src/mcp_coder/utils/jenkins_operations/__init__.py",
    content=<content from DATA section above>
)
```

---

### File 2: Modify utils/__init__.py

**Current Structure Pattern (reference):**
```python
"""Utils package with various utility functions."""

# Import from submodules
from .clipboard import (...)
from .git_operations import (...)
from .github_operations import (...)
# ... more imports

__all__ = [
    # Clipboard operations
    "...",
    # Git operations
    "...",
    # GitHub operations  
    "...",
    # ... more categories
]
```

**Changes to make:**

1. **Add import statement** (after github_operations import):
```python
from .jenkins_operations import (
    JenkinsAuthError,
    JenkinsClient,
    JenkinsConnectionError,
    JenkinsError,
    JenkinsJobNotFoundError,
    JobStatus,
    QueueSummary,
)
```

2. **Add to __all__ list** (after GitHub operations section):
```python
__all__ = [
    # ... existing categories ...
    # GitHub operations
    "PullRequestManager",
    "IssueManager",
    "IssueBranchManager",
    "LabelsManager",
    # Jenkins operations
    "JenkinsClient",
    "JobStatus",
    "QueueSummary",
    "JenkinsError",
    "JenkinsConnectionError",
    "JenkinsAuthError",
    "JenkinsJobNotFoundError",
    # ... rest of existing exports
]
```

**Use MCP tool to edit:**
```python
# First, read the file to see current structure
mcp__filesystem__read_file("src/mcp_coder/utils/__init__.py")

# Then use edit_file to make changes
mcp__filesystem__edit_file(
    file_path="src/mcp_coder/utils/__init__.py",
    edits=[
        {
            "old_text": <find existing import section>,
            "new_text": <same section with jenkins_operations import added>
        },
        {
            "old_text": <find existing __all__ list>,
            "new_text": <same list with jenkins exports added>
        }
    ]
)
```

---

## Validation Steps

After implementation, verify:

1. **Test imports work:**
   ```python
   # Create small test script or use Python REPL
   from mcp_coder.utils import JenkinsClient, JobStatus, QueueSummary
   from mcp_coder.utils import JenkinsError, JenkinsConnectionError
   
   # Verify classes are imported correctly
   assert JenkinsClient is not None
   assert JobStatus is not None
   assert QueueSummary is not None
   
   # Verify exceptions are imported
   assert issubclass(JenkinsConnectionError, JenkinsError)
   ```

2. **Run mypy on updated files:**
   ```python
   mcp__code-checker__run_mypy_check(
       target_directories=["src/mcp_coder/utils/jenkins_operations", "src/mcp_coder/utils"]
   )
   ```

3. **Run pylint on updated files:**
   ```python
   mcp__code-checker__run_pylint_check(
       target_directories=["src/mcp_coder/utils/jenkins_operations"]
   )
   ```

4. **Verify __all__ exports:**
   ```python
   # Check that __all__ matches actual exports
   from mcp_coder.utils.jenkins_operations import __all__
   
   expected = [
       "JenkinsClient",
       "JobStatus",
       "QueueSummary",
       "JenkinsAuthError",
       "JenkinsConnectionError",
       "JenkinsError",
       "JenkinsJobNotFoundError",
   ]
   
   assert set(__all__) == set(expected)
   ```

5. **Quick smoke test:**
   ```python
   # Verify basic import and usage
   from mcp_coder.utils import JenkinsClient
   
   # This should fail with ValueError (expected - validates init logic)
   try:
       client = JenkinsClient("", "", "")
       assert False, "Should have raised ValueError"
   except ValueError:
       pass  # Expected
   ```

---

## Expected Outcomes

✅ **Files created:**
- `src/mcp_coder/utils/jenkins_operations/__init__.py` (~60 lines)

✅ **Files modified:**
- `src/mcp_coder/utils/__init__.py` (added ~10 lines)

✅ **Public API available:**
- Can import from `mcp_coder.utils.jenkins_operations`
- Can import from `mcp_coder.utils`
- All public classes and exceptions accessible
- Private helpers not exposed

✅ **Type checking passes:**
- mypy clean on jenkins_operations package
- No import errors

✅ **Linting passes:**
- pylint clean
- No unused imports
- __all__ is properly defined

---

## Import Test Example

**Create simple test to verify exports:**

```python
"""Quick test to verify jenkins_operations exports."""

def test_jenkins_operations_exports() -> None:
    """Verify all jenkins_operations exports are accessible."""
    # Direct imports
    from mcp_coder.utils.jenkins_operations import (
        JenkinsAuthError,
        JenkinsClient,
        JenkinsConnectionError,
        JenkinsError,
        JenkinsJobNotFoundError,
        JobStatus,
        QueueSummary,
    )
    
    # Via utils package
    from mcp_coder.utils import (
        JenkinsAuthError as JenkinsAuthError2,
        JenkinsClient as JenkinsClient2,
    )
    
    # Verify they're the same classes
    assert JenkinsClient is JenkinsClient2
    assert JenkinsAuthError is JenkinsAuthError2
    
    # Verify exception hierarchy
    assert issubclass(JenkinsConnectionError, JenkinsError)
    assert issubclass(JenkinsAuthError, JenkinsError)
    assert issubclass(JenkinsJobNotFoundError, JenkinsError)
    
    print("✅ All jenkins_operations exports verified")

if __name__ == "__main__":
    test_jenkins_operations_exports()
```

---

## Next Step

After Step 4 is complete and imports work correctly, proceed to:
- **Step 5:** Final quality checks and validation
