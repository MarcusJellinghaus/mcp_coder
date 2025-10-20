# Step 2: Jenkins Client and Unit Tests (TDD)

## LLM Prompt

```
You are implementing Step 2 of the Jenkins Job Automation feature for the mcp_coder project.

Read the following files to understand the context:
1. pr_info/steps/summary.md - Overall implementation summary
2. pr_info/steps/step_1.md - Previous step (models)
3. This step file (pr_info/steps/step_2.md) - Current step details

Your task:
- Follow Test-Driven Development (TDD)
- Create client tests FIRST with mocked python-jenkins library
- Then implement JenkinsClient to pass all tests
- Use MCP filesystem tools (mcp__filesystem__save_file) for all file operations
- Follow patterns from src/mcp_coder/utils/github_operations/base_manager.py
- Use structlog and @log_function_call decorator
- After implementation, run: mcp__code-checker__run_pytest_check with the new test file

Important:
- Mock the python-jenkins library using unittest.mock
- Test configuration reading with env var priority
- Test error handling with custom exceptions
- Keep implementation simple (KISS principle)
```

---

## Objective
Create JenkinsClient class with configuration, API methods, and comprehensive unit tests using TDD approach.

---

## WHERE: File Paths

### Test File (Create FIRST):
```
tests/utils/jenkins_operations/test_client.py
```

### Source File (Create SECOND):
```
src/mcp_coder/utils/jenkins_operations/client.py
```

---

## WHAT: Main Components

### 1. Custom Exception

**Location:** Top of `client.py`

```python
class JenkinsError(Exception):
    """Base exception for Jenkins operations.
    
    All Jenkins-related errors are wrapped in this exception type.
    This keeps error handling simple while providing clear context.
    """
    pass
```

### 2. Configuration Helper Function

**Signature:**
```python
def _get_jenkins_config() -> dict[str, Optional[str]]:
    """Get Jenkins configuration from environment or config file.
    
    Priority: Environment variables > Config file > None
    
    Environment Variables:
        JENKINS_URL: Jenkins server URL with port
        JENKINS_USER: Jenkins username
        JENKINS_TOKEN: Jenkins API token
    
    Config File (~/.mcp_coder/config.toml):
        [jenkins]
        server_url = "https://jenkins.example.com:8080"
        username = "user"
        api_token = "token"
    
    Returns:
        Dict with keys: server_url, username, api_token
        Values are None if not configured
    
    Note:
        test_job is NOT included here - it's only for integration tests
        and is handled separately in the test fixture.
    """
```

**Purpose:** Read Jenkins configuration with environment variable priority.

### 3. JenkinsClient Class

**Main Methods:**

```python
class JenkinsClient:
    """Jenkins job automation client.
    
    Provides methods to start jobs, check status, and monitor queue.
    Uses python-jenkins library for API communication.
    """
    
    def __init__(self, server_url: str, username: str, api_token: str) -> None:
        """Initialize Jenkins client with credentials."""
        
    def start_job(self, job_path: str, params: Optional[dict] = None) -> int:
        """Start a Jenkins job and return queue ID."""
        
    def get_job_status(self, queue_id: int) -> JobStatus:
        """Get job status by queue ID."""
        
    def get_queue_summary(self) -> QueueSummary:
        """Get summary of Jenkins queue."""
```

---

## HOW: Integration Points

### Imports Required:

**For client.py:**
```python
import os
import structlog
from typing import Optional
from jenkins import Jenkins  # python-jenkins library

from mcp_coder.utils import get_config_value
from mcp_coder.utils.log_utils import log_function_call
from .models import JobStatus, QueueSummary
```

**For test_client.py:**
```python
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from jenkins import JenkinsException

from mcp_coder.utils.jenkins_operations.client import (
    JenkinsClient,
    JenkinsError,
    _get_jenkins_config,
)
from mcp_coder.utils.jenkins_operations.models import JobStatus, QueueSummary
```

### Decorators:
- `@log_function_call` - On all public methods for automatic logging

### Pattern References:
- Configuration: `src/mcp_coder/utils/user_config.py`
- API Client: `src/mcp_coder/utils/github_operations/base_manager.py`
- Error Handling: `src/mcp_coder/utils/github_operations/base_manager.py` (_handle_github_errors)

---

## ALGORITHM: Core Logic

### _get_jenkins_config() Algorithm:
```python
1. Check env vars: JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
2. For each missing env var, check config file with get_config_value("jenkins", key)
3. Return dict: {server_url, username, api_token}
4. Values are None if not configured
```

### JenkinsClient.__init__() Algorithm:
```python
1. Validate server_url, username, api_token are non-empty
2. Raise ValueError if any required param is None or empty
3. Create Jenkins client: Jenkins(server_url, username, api_token, timeout=30)
4. Store client as self._client
5. No connection test (lazy validation)
```

### start_job() Algorithm:
```python
1. Default params to {} if None
2. Try: queue_id = self._client.build_job(job_path, parameters=params)
3. Catch JenkinsException or any exception: wrap in JenkinsError with context
4. Log success at debug level
5. Return queue_id
```

**Note:** We wrap ALL exceptions as JenkinsError (KISS principle). The error message from python-jenkins provides sufficient context.

### get_job_status() Algorithm:
```python
1. Try: item = self._client.get_queue_item(queue_id)
2. If item["executable"]: build running/completed
   - Extract build_number, get build_info for duration and url
   - Pass through status string as-is from Jenkins (no validation)
3. Else if item["why"]: still queued
   - Return JobStatus(status="queued", build_number=None, ...)
4. Catch exceptions: wrap in JenkinsError
5. Return JobStatus dataclass
```

**Note:** Status strings are passed through as-is from Jenkins API (forward-compatible with new statuses).

### get_queue_summary() Algorithm:
```python
1. Get queue info: queue = self._client.get_queue_info()
2. Get running builds: builds = self._client.get_running_builds()
3. Count queued items: len(queue)
4. Count running items: len(builds)
5. Return QueueSummary(running=count, queued=count)
```

---

## DATA: Return Values and Structures

### _get_jenkins_config() Return:
```python
{
    "server_url": "https://jenkins.example.com:8080",  # or None
    "username": "jenkins-user",                         # or None
    "api_token": "token123",                            # or None
}
```

### start_job() Return:
```python
# Returns: int (queue ID)
queue_id = client.start_job("folder/job-name", {"PARAM": "value"})
# Example: 12345
```

### get_job_status() Return:
```python
# Returns: JobStatus dataclass
JobStatus(
    status="SUCCESS",
    build_number=42,
    duration_ms=12340,
    url="https://jenkins.example.com/job/test/42"
)
```

### get_queue_summary() Return:
```python
# Returns: QueueSummary dataclass
QueueSummary(running=3, queued=2)
```

---

## Test Implementation (CREATE FIRST)

### File: tests/utils/jenkins_operations/test_client.py

**Test Classes:**

```python
class TestGetJenkinsConfig:
    """Tests for _get_jenkins_config helper."""
    
    def test_config_from_env_vars(self, monkeypatch):
        """Test configuration from environment variables."""
        
    def test_config_from_config_file(self, monkeypatch):
        """Test configuration from config file."""
        
    def test_config_env_priority(self, monkeypatch):
        """Test environment variables take priority."""
        
    def test_config_missing_returns_none(self, monkeypatch):
        """Test missing config returns None values."""


class TestJenkinsClientInit:
    """Tests for JenkinsClient initialization."""
    
    def test_init_success(self):
        """Test successful initialization."""
        
    def test_init_missing_server_url(self):
        """Test initialization fails with missing server_url."""
        
    def test_init_missing_username(self):
        """Test initialization fails with missing username."""
        
    def test_init_missing_api_token(self):
        """Test initialization fails with missing api_token."""
        
    def test_init_empty_string_values(self):
        """Test initialization fails with empty strings."""


class TestJenkinsClientStartJob:
    """Tests for JenkinsClient.start_job method."""
    
    def test_start_job_success(self):
        """Test successful job start returns queue ID."""
        
    def test_start_job_with_params(self):
        """Test starting job with parameters."""
        
    def test_start_job_folder_path(self):
        """Test starting job with folder path."""
        
    def test_start_job_jenkins_error(self):
        """Test JenkinsException is wrapped as JenkinsError."""
        
    def test_start_job_generic_error(self):
        """Test generic exceptions are wrapped as JenkinsError."""


class TestJenkinsClientGetJobStatus:
    """Tests for JenkinsClient.get_job_status method."""
    
    def test_get_job_status_queued(self):
        """Test job status when queued."""
        
    def test_get_job_status_running(self):
        """Test job status when running."""
        
    def test_get_job_status_success(self):
        """Test job status when completed successfully."""
        
    def test_get_job_status_failure(self):
        """Test job status when failed."""
        
    def test_get_job_status_error(self):
        """Test errors are wrapped as JenkinsError."""


class TestJenkinsClientGetQueueSummary:
    """Tests for JenkinsClient.get_queue_summary method."""
    
    def test_get_queue_summary_success(self):
        """Test successful queue summary retrieval."""
        
    def test_get_queue_summary_empty(self):
        """Test queue summary with no jobs."""
        
    def test_get_queue_summary_error(self):
        """Test errors are wrapped as JenkinsError."""
```

**Key Test Patterns:**

1. **Mock python-jenkins:**
   ```python
   @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
   def test_start_job_success(self, mock_jenkins_class):
       mock_client = Mock()
       mock_jenkins_class.return_value = mock_client
       mock_client.build_job.return_value = 12345
       
       client = JenkinsClient("http://jenkins", "user", "token")
       queue_id = client.start_job("test-job")
       
       assert queue_id == 12345
       mock_client.build_job.assert_called_once_with("test-job", parameters={})
   ```

2. **Mock environment variables:**
   ```python
   def test_config_from_env_vars(self, monkeypatch):
       monkeypatch.setenv("JENKINS_URL", "http://jenkins")
       monkeypatch.setenv("JENKINS_USER", "user")
       # ... test logic
   ```

3. **Mock config file:**
   ```python
   @patch("mcp_coder.utils.jenkins_operations.client.get_config_value")
   def test_config_from_config_file(self, mock_get_config):
       mock_get_config.side_effect = lambda sec, key: {
           ("jenkins", "server_url"): "http://jenkins",
           ("jenkins", "username"): "user",
       }.get((sec, key))
       # ... test logic
   ```

**Total Tests:** ~18-20 tests

---

## Source Implementation (CREATE SECOND)

### File: src/mcp_coder/utils/jenkins_operations/client.py

**Module Structure:**

```python
"""Jenkins job automation client.

This module provides the JenkinsClient class for interacting with Jenkins
to start jobs, check status, and monitor the queue.

Tested with Jenkins 2.4xx series.

Configuration:
    ~/.mcp_coder/config.toml:
        [jenkins]
        server_url = "https://jenkins.example.com:8080"
        username = "jenkins-user"
        api_token = "your-api-token"
    
    Environment Variables (override config):
        JENKINS_URL, JENKINS_USER, JENKINS_TOKEN

Limitations:
    - Not designed for concurrent use (create separate instances per thread if needed)
    - 30-second timeout for all operations (not configurable)
    - All errors wrapped as JenkinsError (check error message for details)

Example:
    >>> from mcp_coder.utils.jenkins_operations import JenkinsClient
    >>> client = JenkinsClient("http://jenkins:8080", "user", "token")
    >>> queue_id = client.start_job("my-job", {"PARAM": "value"})
    >>> status = client.get_job_status(queue_id)
    >>> print(status)
    Job #42: SUCCESS (1234ms)
"""
```

**Implementation Order:**

1. **Imports** (structlog, jenkins, typing, utils)
2. **Logger setup:** `logger = structlog.get_logger(__name__)`
3. **Custom exception** (1 exception class: JenkinsError)
4. **_get_jenkins_config()** helper function
5. **JenkinsClient class:**
   - `__init__()` method
   - `start_job()` method with `@log_function_call`
   - `get_job_status()` method with `@log_function_call`
   - `get_queue_summary()` method with `@log_function_call`

**Key Implementation Details:**

- **Timeout:** Fixed 30 seconds in Jenkins() constructor
- **Error Wrapping:** Wrap all exceptions as JenkinsError with context
- **Logging:** Debug level for success, error level for failures
- **Parameters:** Default to `{}` for `start_job()` params
- **Build Status Mapping:** Map Jenkins result strings to status field

---

## Validation Steps

After implementation, verify:

1. **Run tests:**
   ```python
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-v", "tests/utils/jenkins_operations/test_client.py"]
   )
   ```

2. **Expected output:**
   - All ~20-25 tests pass
   - No import errors
   - Coverage for all methods

3. **Run mypy:**
   ```python
   mcp__code-checker__run_mypy_check(
       target_directories=["src/mcp_coder/utils/jenkins_operations"]
   )
   ```

4. **Run pylint:**
   ```python
   mcp__code-checker__run_pylint_check(
       target_directories=["src/mcp_coder/utils/jenkins_operations"]
   )
   ```

---

## Expected Outcomes

✅ **Files created:**
- `tests/utils/jenkins_operations/test_client.py` (~250-300 lines)
- `src/mcp_coder/utils/jenkins_operations/client.py` (~250-300 lines)

✅ **All tests pass** (~18-20 tests)

✅ **Type checking passes** (mypy clean)

✅ **Linting passes** (pylint clean)

✅ **Client features:**
- Configuration from env vars and config file
- Start jobs with optional parameters
- Get detailed job status
- Get queue summary
- Simple exception handling (all wrapped as JenkinsError)
- Structured logging with @log_function_call

---

## Next Step

After Step 2 is complete and all tests pass, proceed to:
- **Step 3:** Integration tests with real Jenkins server
