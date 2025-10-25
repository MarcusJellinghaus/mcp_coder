# Step 2: Repository Config Validation (TDD)

## Overview
Implement repository configuration validation logic to ensure requested repos have all required fields. This provides helpful error messages when configuration is incomplete or missing.

## LLM Prompt
```
You are implementing Step 2 of the "mcp-coder coordinator test" feature.

Read pr_info/steps/summary.md for context.

Your task: Implement repository configuration validation following TDD.

Requirements:
1. Write tests FIRST in tests/cli/commands/test_coordinator.py (new file)
2. Add validation helpers to src/mcp_coder/cli/commands/coordinator.py (new file)
3. Ensure tests pass
4. Run code quality checks

Follow the specifications in this step file exactly.
```

## Phase 2A: Write Tests First (TDD)

### WHERE
File: `tests/cli/commands/test_coordinator.py` (NEW FILE)

### WHAT
Test classes and methods:

```python
"""Tests for coordinator CLI command."""

import pytest
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

from mcp_coder.cli.commands.coordinator import (
    load_repo_config,
    validate_repo_config,
    get_jenkins_credentials,
    format_job_output,
)


class TestLoadRepoConfig:
    """Tests for load_repo_config function."""
    
    def test_load_repo_config_success() -> None:
        """Test successful loading of repository configuration."""
        
    def test_load_repo_config_missing_repo() -> None:
        """Test error when repository doesn't exist in config."""
        
    def test_load_repo_config_handles_missing_config_file() -> None:
        """Test graceful handling when config file doesn't exist."""


class TestValidateRepoConfig:
    """Tests for validate_repo_config function."""
    
    def test_validate_repo_config_complete() -> None:
        """Test validation passes for complete configuration."""
        
    def test_validate_repo_config_missing_repo_url() -> None:
        """Test validation fails when repo_url is missing."""
        
    def test_validate_repo_config_missing_test_job_path() -> None:
        """Test validation fails when test_job_path is missing."""
        
    def test_validate_repo_config_missing_github_credentials_id() -> None:
        """Test validation fails when github_credentials_id is missing."""
        
    def test_validate_repo_config_none_value() -> None:
        """Test validation handles None repository config."""


class TestGetJenkinsCredentials:
    """Tests for get_jenkins_credentials function."""
    
    def test_get_jenkins_credentials_from_env() -> None:
        """Test loading credentials from environment variables."""
        
    def test_get_jenkins_credentials_from_config() -> None:
        """Test loading credentials from config file."""
        
    def test_get_jenkins_credentials_missing_server_url() -> None:
        """Test error when server_url is missing."""
        
    def test_get_jenkins_credentials_missing_username() -> None:
        """Test error when username is missing."""
        
    def test_get_jenkins_credentials_missing_api_token() -> None:
        """Test error when api_token is missing."""


class TestFormatJobOutput:
    """Tests for format_job_output function."""
    
    def test_format_job_output_with_url() -> None:
        """Test formatting output when job URL is available."""
        
    def test_format_job_output_without_url() -> None:
        """Test formatting output when job URL is not yet available."""
```

### HOW
Integration points:
- Import functions from `mcp_coder.cli.commands.coordinator`
- Use `unittest.mock.patch` to mock `get_config_value()`
- Use `pytest.MonkeyPatch` for environment variables
- Use `pytest.raises` for error validation

### ALGORITHM (Test Logic)
```
1. Mock get_config_value() to return test config data
2. Call validation functions with test data
3. Assert correct return values or raised exceptions
4. Verify error messages are helpful
5. Test all edge cases (missing fields, None values, etc.)
```

### DATA

**load_repo_config() returns**:
```python
Optional[dict[str, str]]
# Example: {"repo_url": "...", "test_job_path": "...", "github_credentials_id": "..."}
# Or None if repo not found
```

**validate_repo_config() raises**:
```python
ValueError  # With helpful message about missing field
```

**get_jenkins_credentials() returns**:
```python
tuple[str, str, str]  # (server_url, username, api_token)
# Raises ValueError if any credential missing
```

**format_job_output() returns**:
```python
str  # Formatted output message
```

### Test Example Structure
```python
@patch("mcp_coder.cli.commands.coordinator.get_config_value")
def test_load_repo_config_success(mock_get_config: MagicMock) -> None:
    """Test successful loading of repository configuration."""
    # Setup
    def config_side_effect(section: str, key: str) -> str | None:
        config_map = {
            ("coordinator.repos.mcp_coder", "repo_url"): "https://github.com/user/repo.git",
            ("coordinator.repos.mcp_coder", "test_job_path"): "Folder/job-name",
            ("coordinator.repos.mcp_coder", "github_credentials_id"): "github-pat",
        }
        return config_map.get((section, key))
    
    mock_get_config.side_effect = config_side_effect
    
    # Execute
    result = load_repo_config("mcp_coder")
    
    # Verify
    assert result is not None
    assert result["repo_url"] == "https://github.com/user/repo.git"
    assert result["test_job_path"] == "Folder/job-name"
    assert result["github_credentials_id"] == "github-pat"
```

## Phase 2B: Implement Functionality

### WHERE
File: `src/mcp_coder/cli/commands/coordinator.py` (NEW FILE)

### WHAT
Create new file with these functions:

```python
"""Coordinator CLI command implementation.

This module provides the coordinator test command for triggering
Jenkins-based integration tests for MCP Coder repositories.
"""

import argparse
import logging
import os
from typing import Optional

from ...utils.user_config import get_config_value
from ...utils.jenkins_operations import JenkinsClient

logger = logging.getLogger(__name__)


def load_repo_config(repo_name: str) -> Optional[dict[str, str]]:
    """Load repository configuration from config file.
    
    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")
        
    Returns:
        Dictionary with repo_url, test_job_path, github_credentials_id
        or None if repository not found in config
    """
    

def validate_repo_config(repo_name: str, config: Optional[dict[str, str]]) -> None:
    """Validate repository configuration has all required fields.
    
    Args:
        repo_name: Name of repository being validated
        config: Repository configuration dict or None
        
    Raises:
        ValueError: If config is None or missing required fields
    """
    

def get_jenkins_credentials() -> tuple[str, str, str]:
    """Get Jenkins credentials from environment or config file.
    
    Priority: Environment variables > Config file
    
    Returns:
        Tuple of (server_url, username, api_token)
        
    Raises:
        ValueError: If any required credential is missing
    """
    

def format_job_output(job_path: str, queue_id: int, url: Optional[str]) -> str:
    """Format job trigger output message.
    
    Args:
        job_path: Jenkins job path
        queue_id: Queue ID from Jenkins
        url: Job URL if available (may be None if not started yet)
        
    Returns:
        Formatted output string
    """
```

### HOW
Integration points:
- Import `get_config_value` from `utils.user_config`
- Import `JenkinsClient` from `utils.jenkins_operations`
- Use `logging` for debug information
- Import `os` for environment variable access

### ALGORITHM

**load_repo_config()**:
```
1. Construct config section: f"coordinator.repos.{repo_name}"
2. Read repo_url, test_job_path, github_credentials_id using get_config_value()
3. If all three exist, return dict with values
4. Otherwise return None
```

**validate_repo_config()**:
```
1. If config is None, raise ValueError with helpful message
2. Check each required field: repo_url, test_job_path, github_credentials_id
3. If any missing, raise ValueError with field name in message
4. If all present, return (validation passed)
```

**get_jenkins_credentials()**:
```
1. Read env vars: JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
2. For missing env vars, read from config: jenkins.server_url, jenkins.username, jenkins.api_token
3. If any still missing, raise ValueError with helpful message
4. Return tuple of (server_url, username, api_token)
```

**format_job_output()**:
```
1. Create first line: f"Job triggered: {job_path} - test - queue: {queue_id}"
2. If url is not None, add second line with URL
3. Return formatted string
```

### DATA

**load_repo_config()**:
- Input: `repo_name: str`
- Output: `Optional[dict[str, str]]`
- Keys in dict: `"repo_url"`, `"test_job_path"`, `"github_credentials_id"`

**validate_repo_config()**:
- Input: `repo_name: str`, `config: Optional[dict[str, str]]`
- Output: `None` (raises on error)
- Raises: `ValueError` with messages like:
  - `"Repository 'repo_name' not found in config"`
  - `"Repository 'repo_name' missing required field 'field_name'"`

**get_jenkins_credentials()**:
- Input: None
- Output: `tuple[str, str, str]`
- Raises: `ValueError` with message like:
  - `"Jenkins configuration incomplete. Missing: server_url, username"`

**format_job_output()**:
- Input: `job_path: str`, `queue_id: int`, `url: Optional[str]`
- Output: `str`
- Examples:
  ```
  "Job triggered: MCP_Coder/test-job - test - queue: 12345\nhttps://jenkins.example.com/job/MCP_Coder/test-job/42/"
  ```
  or without URL:
  ```
  "Job triggered: MCP_Coder/test-job - test - queue: 12345\nhttps://jenkins.example.com/queue/item/12345/"
  ```

### Implementation Skeleton

```python
def load_repo_config(repo_name: str) -> Optional[dict[str, str]]:
    """Load repository configuration from config file."""
    section = f"coordinator.repos.{repo_name}"
    
    repo_url = get_config_value(section, "repo_url")
    test_job_path = get_config_value(section, "test_job_path")
    github_credentials_id = get_config_value(section, "github_credentials_id")
    
    # Return dict only if all values present
    if repo_url and test_job_path and github_credentials_id:
        return {
            "repo_url": repo_url,
            "test_job_path": test_job_path,
            "github_credentials_id": github_credentials_id,
        }
    
    return None


def validate_repo_config(repo_name: str, config: Optional[dict[str, str]]) -> None:
    """Validate repository configuration has all required fields."""
    if config is None:
        raise ValueError(
            f"Repository '{repo_name}' not found in config\n"
            f"Add it to config file under [coordinator.repos.{repo_name}]"
        )
    
    required_fields = ["repo_url", "test_job_path", "github_credentials_id"]
    for field in required_fields:
        if field not in config or not config[field]:
            raise ValueError(
                f"Repository '{repo_name}' missing required field '{field}'"
            )


def get_jenkins_credentials() -> tuple[str, str, str]:
    """Get Jenkins credentials from environment or config file."""
    # Priority: env vars > config file
    server_url = os.getenv("JENKINS_URL") or get_config_value("jenkins", "server_url")
    username = os.getenv("JENKINS_USER") or get_config_value("jenkins", "username")
    api_token = os.getenv("JENKINS_TOKEN") or get_config_value("jenkins", "api_token")
    
    # Check for missing credentials
    missing = []
    if not server_url:
        missing.append("server_url")
    if not username:
        missing.append("username")
    if not api_token:
        missing.append("api_token")
    
    if missing:
        raise ValueError(
            f"Jenkins configuration incomplete. Missing: {', '.join(missing)}\n"
            f"Set via environment variables (JENKINS_URL, JENKINS_USER, JENKINS_TOKEN) "
            f"or config file [jenkins] section"
        )
    
    return (server_url, username, api_token)


def format_job_output(job_path: str, queue_id: int, url: Optional[str]) -> str:
    """Format job trigger output message."""
    output = f"Job triggered: {job_path} - test - queue: {queue_id}"
    
    if url:
        output += f"\n{url}"
    else:
        # Construct queue URL if job URL not available yet
        # Note: This is a fallback - actual implementation may vary
        output += f"\n(Job URL will be available once build starts)"
    
    return output
```

## Phase 2C: Verify Implementation

### Manual Verification Steps
1. Run tests: `pytest tests/cli/commands/test_coordinator.py -v`
2. Verify all tests pass
3. Check test coverage for new functions

### Expected Test Output
```
tests/cli/commands/test_coordinator.py::TestLoadRepoConfig::test_load_repo_config_success PASSED
tests/cli/commands/test_coordinator.py::TestLoadRepoConfig::test_load_repo_config_missing_repo PASSED
tests/cli/commands/test_coordinator.py::TestLoadRepoConfig::test_load_repo_config_handles_missing_config_file PASSED
tests/cli/commands/test_coordinator.py::TestValidateRepoConfig::test_validate_repo_config_complete PASSED
tests/cli/commands/test_coordinator.py::TestValidateRepoConfig::test_validate_repo_config_missing_repo_url PASSED
tests/cli/commands/test_coordinator.py::TestValidateRepoConfig::test_validate_repo_config_missing_test_job_path PASSED
tests/cli/commands/test_coordinator.py::TestValidateRepoConfig::test_validate_repo_config_missing_github_credentials_id PASSED
tests/cli/commands/test_coordinator.py::TestValidateRepoConfig::test_validate_repo_config_none_value PASSED
tests/cli/commands/test_coordinator.py::TestGetJenkinsCredentials::test_get_jenkins_credentials_from_env PASSED
tests/cli/commands/test_coordinator.py::TestGetJenkinsCredentials::test_get_jenkins_credentials_from_config PASSED
tests/cli/commands/test_coordinator.py::TestGetJenkinsCredentials::test_get_jenkins_credentials_missing_server_url PASSED
tests/cli/commands/test_coordinator.py::TestGetJenkinsCredentials::test_get_jenkins_credentials_missing_username PASSED
tests/cli/commands/test_coordinator.py::TestGetJenkinsCredentials::test_get_jenkins_credentials_missing_api_token PASSED
tests/cli/commands/test_coordinator.py::TestFormatJobOutput::test_format_job_output_with_url PASSED
tests/cli/commands/test_coordinator.py::TestFormatJobOutput::test_format_job_output_without_url PASSED

15 passed
```

## Phase 2D: Code Quality Checks

Run mandatory code quality checks:

```python
# Pylint
mcp__code-checker__run_pylint_check()

# Pytest (fast unit tests)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not jenkins_integration and not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Mypy
mcp__code-checker__run_mypy_check()
```

All checks must pass before proceeding to Step 3.

## Success Criteria

- ✅ All 15 tests pass
- ✅ load_repo_config() returns dict with all fields or None
- ✅ validate_repo_config() raises helpful ValueError messages
- ✅ get_jenkins_credentials() respects env var priority
- ✅ get_jenkins_credentials() has helpful error messages
- ✅ format_job_output() creates expected output format
- ✅ Pylint: No errors
- ✅ Pytest: All tests pass
- ✅ Mypy: No type errors

## Files Created/Modified

### New Files:
- `tests/cli/commands/test_coordinator.py` (~200-250 lines)
- `src/mcp_coder/cli/commands/coordinator.py` (~100-130 lines)

### Total Lines: ~300-380 lines

## Next Step
After all checks pass, proceed to **Step 3: CLI Command Core Logic**.
