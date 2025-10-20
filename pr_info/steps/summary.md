# Jenkins Job Automation - Implementation Summary

## Overview
Add Python utilities to interact with Jenkins for job automation, including starting jobs, checking status, and monitoring the queue.

**Issue:** #136  
**Branch:** `136-jenkins-jobs-triggering---from-python`

---

## Architecture & Design Changes

### 1. New Module Structure
Following existing patterns from `git_operations/` and `github_operations/`, we're adding a new utility subpackage:

```
src/mcp_coder/utils/jenkins_operations/
  ├── __init__.py        # Public API exports
  ├── client.py          # JenkinsClient class + exceptions + config
  └── models.py          # JobStatus, QueueSummary dataclasses
```

### 2. Design Decisions (KISS Principle Applied)

#### **Simplification 1: Consolidated Module Structure**
- ❌ **Rejected:** Separate `config.py`, `exceptions.py` modules
- ✅ **Chosen:** Merge config helper and exceptions into `client.py`
- **Rationale:** Only 4 config values and 4 exceptions - don't need separate files. Keeps related code together for easier maintenance.

#### **Simplification 2: Lazy Validation**
- ❌ **Rejected:** Connection test on client initialization
- ✅ **Chosen:** Let first API call discover connection issues
- **Rationale:** Faster initialization, simpler code. Connection errors will surface naturally on first use.

#### **Simplification 3: Minimal Job Path Validation**
- ❌ **Rejected:** Custom job path parsing and validation
- ✅ **Chosen:** Pass paths to Jenkins API, let it validate
- **Rationale:** Don't duplicate `python-jenkins` library validation logic. Single source of truth.

#### **Simplification 4: Consolidated Test Files**
- ❌ **Rejected:** Separate `test_exceptions.py`, `test_config.py`
- ✅ **Chosen:** Test config in `test_client.py`, skip exception tests
- **Rationale:** Testing simple class definitions adds no value. Config is tested via client initialization.

### 3. Core Components

#### **3.1 Models (`models.py`)**
Two dataclasses following existing `CommitResult`, `PushResult` pattern:

```python
@dataclass
class JobStatus:
    status: str                      # "queued", "running", "SUCCESS", "FAILURE", etc.
    build_number: Optional[int]
    duration_ms: Optional[int]
    url: Optional[str]
    
    def __str__(self) -> str:
        # Human-readable format: "Job #42: SUCCESS (1234ms)"
```

```python
@dataclass
class QueueSummary:
    running: int
    queued: int
    
    def __str__(self) -> str:
        # Format: "3 jobs running, 2 jobs queued"
```

#### **3.2 Client (`client.py`)**

**Custom Exceptions:**
```python
class JenkinsError(Exception): pass
class JenkinsConnectionError(JenkinsError): pass
class JenkinsAuthError(JenkinsError): pass
class JenkinsJobNotFoundError(JenkinsError): pass
```

**Configuration Helper:**
```python
def _get_jenkins_config() -> dict:
    """Priority: env vars > config file > defaults"""
    # Check JENKINS_URL, JENKINS_USER, JENKINS_TOKEN, JENKINS_TEST_JOB
    # Fall back to config file [jenkins] section
    # Return dict with server_url, username, api_token, test_job
```

**Main Client Class:**
```python
class JenkinsClient:
    def __init__(self, server_url: str, username: str, api_token: str)
    def start_job(self, job_path: str, params: dict = None) -> int
    def get_job_status(self, queue_id: int) -> JobStatus
    def get_queue_summary(self) -> QueueSummary
```

### 4. Configuration Format

**File:** `~/.mcp_coder/config.toml`

```toml
[jenkins]
server_url = "https://jenkins.example.com:8080"  # Port in URL
username = "jenkins-user"
api_token = "your-api-token-here"
test_job = "mcp-coder-test-job"  # Optional, for integration tests
```

**Environment Variables (override config):**
- `JENKINS_URL` → `server_url`
- `JENKINS_USER` → `username`
- `JENKINS_TOKEN` → `api_token`
- `JENKINS_TEST_JOB` → `test_job`

### 5. Testing Strategy

#### **Test Structure:**
```
tests/utils/jenkins_operations/
  ├── __init__.py
  ├── test_models.py       # Dataclass tests (~30 lines)
  ├── test_client.py       # Unit tests with mocked python-jenkins (~150 lines)
  └── test_integration.py  # @pytest.mark.jenkins_integration (~80 lines)
```

#### **New Pytest Marker:**
```python
[tool.pytest.ini_options]
markers = [
    # ... existing markers ...
    "jenkins_integration: tests requiring Jenkins server access (network, auth needed)",
]
```

#### **TDD Approach:**
1. Write tests first (with mocks)
2. Implement functionality to pass tests
3. Run quality checks (pylint, pytest, mypy)

### 6. Integration Points

#### **6.1 Dependency Addition**
`pyproject.toml` already has:
```toml
dependencies = [
    "python-jenkins>=1.8.0",
    # ... other deps ...
]
```

#### **6.2 Module Exports**
`src/mcp_coder/utils/__init__.py` will add:
```python
from .jenkins_operations import (
    JenkinsClient,
    JobStatus,
    QueueSummary,
    JenkinsError,
    JenkinsConnectionError,
    JenkinsAuthError,
    JenkinsJobNotFoundError,
)

__all__ = [
    # ... existing exports ...
    "JenkinsClient",
    "JobStatus", 
    "QueueSummary",
    "JenkinsError",
    "JenkinsConnectionError",
    "JenkinsAuthError",
    "JenkinsJobNotFoundError",
]
```

#### **6.3 Logging Integration**
Uses existing `structlog` setup from `log_utils.py`:
```python
logger = structlog.get_logger(__name__)

@log_function_call
def start_job(self, job_path: str, params: dict = None) -> int:
    # Automatic logging of: parameters, execution time, return value
```

### 7. Error Handling Pattern

Following `github_operations/base_manager.py` pattern:
- Custom exception hierarchy for specific error types
- Clear error messages with context
- Logging at appropriate levels (debug for success, error for failures)
- Graceful handling of missing configuration

---

## Files to Create or Modify

### **Files to CREATE:**

#### **Source Files (3 new files):**
1. `src/mcp_coder/utils/jenkins_operations/__init__.py`
2. `src/mcp_coder/utils/jenkins_operations/models.py`
3. `src/mcp_coder/utils/jenkins_operations/client.py`

#### **Test Files (4 new files):**
4. `tests/utils/jenkins_operations/__init__.py`
5. `tests/utils/jenkins_operations/test_models.py`
6. `tests/utils/jenkins_operations/test_client.py`
7. `tests/utils/jenkins_operations/test_integration.py`

### **Files to MODIFY:**

#### **Configuration (1 file):**
8. `pyproject.toml` - Add `jenkins_integration` marker

#### **Module Exports (1 file):**
9. `src/mcp_coder/utils/__init__.py` - Add jenkins_operations exports

**Total:** 7 new files, 2 modified files

---

## Implementation Steps Overview

### **Step 1: Models + Tests (TDD)**
- Create `models.py` with dataclasses
- Create `test_models.py` with comprehensive tests
- Run tests (should pass immediately for dataclasses)

### **Step 2: Client + Tests (TDD)**
- Create `test_client.py` with mocked tests
- Create `client.py` with JenkinsClient implementation
- Run tests until all pass

### **Step 3: Integration Tests**
- Create `test_integration.py` with real Jenkins test
- Add `jenkins_integration` marker to `pyproject.toml`
- Document test requirements

### **Step 4: Module Exports & Integration**
- Create `jenkins_operations/__init__.py`
- Update `utils/__init__.py` with exports
- Verify imports work correctly

### **Step 5: Quality Checks & Validation**
- Run `mcp__code-checker__run_pylint_check` (must pass)
- Run `mcp__code-checker__run_pytest_check` with unit tests (must pass)
- Run `mcp__code-checker__run_mypy_check` (must pass)
- Document usage examples

---

## Success Criteria

✅ All issue requirements met:
1. Jenkins client can start jobs and return queue IDs
2. Job status can be retrieved with detailed information
3. Queue summary provides running/queued counts
4. Configuration loaded from `~/.mcp_coder/config.toml`
5. Custom exceptions with clear error messages
6. Unit tests with mocked library
7. Integration test with `@pytest.mark.jenkins_integration`
8. Structured logging using `structlog`
9. Type hints throughout
10. Follows existing project patterns and conventions

✅ KISS principles applied:
- Minimal file structure (3 source files)
- Consolidated related code
- Lazy validation
- Simple, clear implementations

✅ All quality checks pass:
- Pylint (no errors)
- Pytest (all unit tests pass)
- Mypy (type checking passes)

---

## Estimated Complexity

- **Lines of Code:** ~500-600 total
  - `models.py`: ~60 lines
  - `client.py`: ~250 lines
  - Tests: ~260 lines
  - Config/exports: ~30 lines

- **Implementation Time:** 2-4 hours (with TDD)
  
- **Maintenance Burden:** Low (follows existing patterns, well-tested)

---

## References

- **Issue:** #136 - Add Jenkins Job Automation Support
- **Architecture:** `docs/architecture/ARCHITECTURE.md`
- **Similar Patterns:** 
  - `utils/git_operations/` - modular utility package
  - `utils/github_operations/` - API client with managers
  - `utils/user_config.py` - configuration reading
  - `utils/log_utils.py` - logging patterns
