# Step 3: Integration Tests with Real Jenkins

## LLM Prompt

```
You are implementing Step 3 of the Jenkins Job Automation feature for the mcp_coder project.

Read the following files to understand the context:
1. pr_info/steps/summary.md - Overall implementation summary
2. pr_info/steps/step_1.md - Models implementation
3. pr_info/steps/step_2.md - Client implementation
4. This step file (pr_info/steps/step_3.md) - Current step details

Your task:
- Create integration test that uses REAL Jenkins server
- Add @pytest.mark.jenkins_integration marker
- Follow pattern from tests/utils/github_operations/test_github_integration_smoke.py
- Test configuration priority: env vars > config file > skip test
- Use MCP filesystem tools (mcp__filesystem__save_file, mcp__filesystem__edit_file)
- After creating tests, update pyproject.toml with new marker

Important:
- Tests should skip gracefully if Jenkins not configured
- Don't wait for job completion (just verify API calls work)
- Use tmp_path fixture for any temporary files
- Document configuration requirements clearly
```

---

## Objective
Create integration tests that verify JenkinsClient works with a real Jenkins server, with graceful skipping when not configured.

---

## WHERE: File Paths

### Test File (Create):
```
tests/utils/jenkins_operations/test_integration.py
```

### Config File (Modify):
```
pyproject.toml
```

---

## WHAT: Main Components

### 1. Configuration Fixture

**Signature:**
```python
@pytest.fixture
def jenkins_test_setup() -> Generator[dict, None, None]:
    """Provide Jenkins test configuration.
    
    Configuration sources (in priority order):
    1. Environment variables: JENKINS_URL, JENKINS_USER, JENKINS_TOKEN, JENKINS_TEST_JOB
    2. Config file: ~/.mcp_coder/config.toml [jenkins] section
    3. Skip test if neither configured
    
    Yields:
        Dict with: server_url, username, api_token, test_job
        
    Raises:
        pytest.skip: If configuration is missing
    """
```

**Purpose:** Provide Jenkins configuration for integration tests with graceful skipping.

### 2. Client Fixture

**Signature:**
```python
@pytest.fixture
def jenkins_client(jenkins_test_setup: dict) -> JenkinsClient:
    """Create JenkinsClient instance for testing.
    
    Args:
        jenkins_test_setup: Jenkins configuration from fixture
        
    Returns:
        Configured JenkinsClient instance
    """
```

**Purpose:** Create authenticated Jenkins client for tests.

### 3. Integration Test Class

**Test Methods:**
- `test_basic_api_connectivity()` - Verify client can connect
- `test_job_lifecycle()` - Start job, check status, get queue summary

---

## HOW: Integration Points

### Imports Required:

```python
import os
import pytest
from pathlib import Path
from typing import Generator

from mcp_coder.utils.jenkins_operations import (
    JenkinsClient,
    JobStatus,
    QueueSummary,
)
from mcp_coder.utils.jenkins_operations.client import _get_jenkins_config
```

### Decorators:
- `@pytest.fixture` - For configuration and client fixtures
- `@pytest.mark.jenkins_integration` - Mark tests as requiring real Jenkins

### Pattern References:
- Follow: `tests/utils/github_operations/test_github_integration_smoke.py`
- Configuration priority pattern from: `tests/conftest.py` (github_test_setup)

---

## ALGORITHM: Core Logic

### jenkins_test_setup() Fixture Algorithm:
```python
1. Import get_config_value from user_config
2. Check env vars: JENKINS_URL, JENKINS_USER, JENKINS_TOKEN, JENKINS_TEST_JOB
3. For missing env vars, try config file with get_config_value("jenkins", key)
4. If server_url OR username OR api_token missing:
   - Generate detailed skip message showing what's missing
   - Call pytest.skip(message)
5. Default test_job to "mcp-coder-test-job" if not configured
6. Yield config dict: {server_url, username, api_token, test_job}
```

### test_basic_api_connectivity() Algorithm:
```python
1. Get queue summary from client
2. Assert summary is QueueSummary instance
3. Assert running and queued are integers >= 0
4. Print success message with counts
```

### test_job_lifecycle() Algorithm:
```python
1. Get test_job from jenkins_test_setup
2. Start job: queue_id = client.start_job(test_job, params={})
3. Assert queue_id is int > 0
4. Get status: status = client.get_job_status(queue_id)
5. Assert status is JobStatus instance
6. Assert status.status is valid (queued, running, or completed state)
7. Get summary: summary = client.get_queue_summary()
8. Assert summary is QueueSummary instance
9. Print success message with job info
```

---

## DATA: Test Configuration and Results

### jenkins_test_setup Yield:
```python
{
    "server_url": "https://jenkins.example.com:8080",
    "username": "jenkins-user",
    "api_token": "token123",
    "test_job": "mcp-coder-test-job"
}
```

### Expected Test Results:

**test_basic_api_connectivity:**
```python
# Output: QueueSummary(running=3, queued=2)
# Assertions pass if valid integers
```

**test_job_lifecycle:**
```python
# queue_id: 12345
# status: JobStatus(status="queued", build_number=None, ...)
# summary: QueueSummary(running=1, queued=0)
# Assertions pass if valid types and values
```

---

## Test Implementation

### File: tests/utils/jenkins_operations/test_integration.py

**Module Docstring:**
```python
"""Integration tests for Jenkins operations.

These tests verify JenkinsClient works with a real Jenkins server.
Tests are skipped if Jenkins is not configured.

Configuration:
    Environment Variables (highest priority):
        JENKINS_URL: Jenkins server URL with port
        JENKINS_USER: Jenkins username
        JENKINS_TOKEN: Jenkins API token
        JENKINS_TEST_JOB: Test job name (optional, defaults to mcp-coder-test-job)
    
    Config File (~/.mcp_coder/config.toml):
        [jenkins]
        server_url = "https://jenkins.example.com:8080"
        username = "jenkins-user"
        api_token = "your-api-token"
        test_job = "mcp-coder-test-job"

Note:
    Tests will be skipped if configuration is missing.
    Tests DO NOT wait for job completion (just verify API calls work).
"""
```

**Complete Test Structure:**

```python
"""Integration tests for Jenkins operations."""

import os
import pytest
from typing import Generator

from mcp_coder.utils.jenkins_operations import (
    JenkinsClient,
    JobStatus,
    QueueSummary,
)


@pytest.fixture
def jenkins_test_setup() -> Generator[dict, None, None]:
    """Provide Jenkins test configuration.
    
    Configuration sources (in priority order):
    1. Environment variables
    2. Config file
    3. Skip test if neither configured
    
    Yields:
        Dict with server_url, username, api_token, test_job
        
    Raises:
        pytest.skip: If required configuration missing
    """
    from mcp_coder.utils.user_config import get_config_value, get_config_file_path
    
    # Check environment variables first
    server_url = os.getenv("JENKINS_URL")
    username = os.getenv("JENKINS_USER")
    api_token = os.getenv("JENKINS_TOKEN")
    test_job = os.getenv("JENKINS_TEST_JOB")
    
    # Fall back to config file
    config_file_path = get_config_file_path()
    
    if not server_url:
        server_url = get_config_value("jenkins", "server_url")
    if not username:
        username = get_config_value("jenkins", "username")
    if not api_token:
        api_token = get_config_value("jenkins", "api_token")
    if not test_job:
        test_job = get_config_value("jenkins", "test_job")
    
    # Default test_job if still not set
    if not test_job:
        test_job = "mcp-coder-test-job"
    
    # Determine sources for reporting
    url_source = "env" if os.getenv("JENKINS_URL") else "config" if server_url else "none"
    user_source = "env" if os.getenv("JENKINS_USER") else "config" if username else "none"
    token_source = "env" if os.getenv("JENKINS_TOKEN") else "config" if api_token else "none"
    
    print(f"\nJenkins Integration: url={url_source}, user={user_source}, token={token_source}")
    
    # Check required configuration
    if not server_url:
        skip_msg = (
            "Jenkins server URL not configured.\n"
            f"  Environment variable JENKINS_URL: Not found\n"
            f"  Config file location: {config_file_path}\n"
            f"  Config file exists: {config_file_path.exists() if config_file_path else False}\n"
            f"  Config file jenkins.server_url: Not found\n\n"
            "To fix, either:\n"
            "  1. Set environment variable: export JENKINS_URL=https://jenkins.example.com:8080\n"
            f"  2. Add to config file {config_file_path}:\n"
            "     [jenkins]\n"
            '     server_url = "https://jenkins.example.com:8080"'
        )
        pytest.skip(skip_msg)
    
    if not username:
        skip_msg = (
            "Jenkins username not configured.\n"
            f"  Environment variable JENKINS_USER: Not found\n"
            f"  Config file jenkins.username: Not found\n\n"
            "To fix, either:\n"
            "  1. Set environment variable: export JENKINS_USER=jenkins-user\n"
            f"  2. Add to config file {config_file_path}:\n"
            "     [jenkins]\n"
            '     username = "jenkins-user"'
        )
        pytest.skip(skip_msg)
    
    if not api_token:
        skip_msg = (
            "Jenkins API token not configured.\n"
            f"  Environment variable JENKINS_TOKEN: Not found\n"
            f"  Config file jenkins.api_token: Not found\n\n"
            "To fix, either:\n"
            "  1. Set environment variable: export JENKINS_TOKEN=your-token\n"
            f"  2. Add to config file {config_file_path}:\n"
            "     [jenkins]\n"
            '     api_token = "your-token"'
        )
        pytest.skip(skip_msg)
    
    setup = {
        "server_url": server_url,
        "username": username,
        "api_token": api_token,
        "test_job": test_job,
    }
    yield setup


@pytest.fixture
def jenkins_client(jenkins_test_setup: dict) -> JenkinsClient:
    """Create JenkinsClient instance for testing.
    
    Args:
        jenkins_test_setup: Jenkins configuration from fixture
        
    Returns:
        Configured JenkinsClient instance
    """
    return JenkinsClient(
        server_url=jenkins_test_setup["server_url"],
        username=jenkins_test_setup["username"],
        api_token=jenkins_test_setup["api_token"],
    )


@pytest.mark.jenkins_integration
class TestJenkinsIntegration:
    """Integration tests for Jenkins operations with real server."""
    
    def test_basic_api_connectivity(self, jenkins_client: JenkinsClient) -> None:
        """Verify basic Jenkins API connectivity.
        
        This is a minimal smoke test that verifies:
        1. Authentication works
        2. Server access works
        3. Basic queue query works
        """
        # Get queue summary (tests auth + server access)
        summary = jenkins_client.get_queue_summary()
        
        # Verify response structure
        assert isinstance(summary, QueueSummary), "Expected QueueSummary instance"
        assert isinstance(summary.running, int), "Expected running to be int"
        assert isinstance(summary.queued, int), "Expected queued to be int"
        assert summary.running >= 0, "Expected non-negative running count"
        assert summary.queued >= 0, "Expected non-negative queued count"
        
        print(f"\n[OK] Jenkins connectivity verified: {summary}")
    
    def test_job_lifecycle(
        self, jenkins_client: JenkinsClient, jenkins_test_setup: dict
    ) -> None:
        """Verify job lifecycle operations work.
        
        This test verifies:
        1. Job can be started
        2. Queue ID is returned
        3. Job status can be retrieved
        4. Queue summary reflects the job
        
        Note: Does NOT wait for job completion.
        """
        test_job = jenkins_test_setup["test_job"]
        
        # Start job
        queue_id = jenkins_client.start_job(test_job)
        assert isinstance(queue_id, int), "Expected queue_id to be int"
        assert queue_id > 0, "Expected positive queue_id"
        print(f"\n[OK] Started job '{test_job}', queue_id={queue_id}")
        
        # Get job status (should be queued or running)
        status = jenkins_client.get_job_status(queue_id)
        assert isinstance(status, JobStatus), "Expected JobStatus instance"
        assert status.status in [
            "queued", "running", "SUCCESS", "FAILURE", "ABORTED", "UNSTABLE"
        ], f"Unexpected status: {status.status}"
        print(f"[OK] Job status: {status}")
        
        # Get queue summary
        summary = jenkins_client.get_queue_summary()
        assert isinstance(summary, QueueSummary), "Expected QueueSummary instance"
        print(f"[OK] Queue summary: {summary}")
```

**Test Characteristics:**
- ~120-150 lines total
- 2 test methods
- Comprehensive skip messages
- Clear success messages
- No waiting for job completion

---

## Configuration Update

### File: pyproject.toml

**Add jenkins_integration marker:**

Use `mcp__filesystem__edit_file` to add the marker to the existing markers list:

```python
# Find this section:
markers = [
    "claude_cli_integration: tests that use real Claude CLI executable (slow)",
    "claude_api_integration: tests that make actual API calls to Claude API (slow)",
    "git_integration: tests with file system git operations (repos, commits)", 
    "checker_integration: tests for code checker integration (pylint, pytest, mypy)",
    "formatter_integration: tests for code formatter integration (black, isort)",
    "github_integration: tests requiring GitHub API access (network, auth needed)",
]

# Add new marker:
markers = [
    "claude_cli_integration: tests that use real Claude CLI executable (slow)",
    "claude_api_integration: tests that make actual API calls to Claude API (slow)",
    "git_integration: tests with file system git operations (repos, commits)", 
    "checker_integration: tests for code checker integration (pylint, pytest, mypy)",
    "formatter_integration: tests for code formatter integration (black, isort)",
    "github_integration: tests requiring GitHub API access (network, auth needed)",
    "jenkins_integration: tests requiring Jenkins server access (network, auth needed)",
]
```

---

## Validation Steps

After implementation, verify:

1. **Run integration tests (will skip if not configured):**
   ```python
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-v", "-m", "jenkins_integration"]
   )
   ```

2. **Expected output if not configured:**
   ```
   SKIPPED - Jenkins server URL not configured.
   ```

3. **Expected output if configured:**
   ```
   test_basic_api_connectivity PASSED
   test_job_lifecycle PASSED
   ```

4. **Verify marker is registered:**
   ```python
   # Run pytest with --markers flag to see all markers
   mcp__code-checker__run_pytest_check(
       extra_args=["--markers"]
   )
   # Should list jenkins_integration in output
   ```

5. **Run all unit tests (should exclude integration):**
   ```python
   mcp__code-checker__run_pytest_check(
       extra_args=[
           "-n", "auto", 
           "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not jenkins_integration"
       ]
   )
   ```

---

## Expected Outcomes

✅ **Files created:**
- `tests/utils/jenkins_operations/test_integration.py` (~120-150 lines)

✅ **Files modified:**
- `pyproject.toml` (added jenkins_integration marker)

✅ **Integration tests:**
- Skip gracefully when Jenkins not configured
- Run successfully when configured
- Verify API connectivity
- Verify job lifecycle operations
- Don't wait for job completion

✅ **Configuration priority:**
- Environment variables take precedence
- Config file is fallback
- Clear skip messages guide setup

---

## Next Step

After Step 3 is complete, proceed to:
- **Step 4:** Module exports and public API setup
