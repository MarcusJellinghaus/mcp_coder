# Step 8: Implement DEFAULT_TEST_COMMAND Constant

## Overview
Replace the hardcoded `"mcp-coder --version"` command with a comprehensive multi-line test script constant. This script verifies the complete environment setup including tools, dependencies, Claude CLI, and MCP Coder functionality.

## LLM Prompt
```
You are implementing Step 8 of the coordinator test command fixes.

Read pr_info/steps/summary.md for context.
Read pr_info/steps/decisions.md for the decision rationale (Issue #3).

Your task: Add DEFAULT_TEST_COMMAND constant and use it in coordinator.py, then document it.

Requirements:
1. Add module-level constant with comprehensive test script
2. Update execute_coordinator_test() to use the constant
3. Write tests for the new behavior (TDD approach)
4. Document the test command in CONFIG.md
5. Run code quality checks

Follow the specifications in this step file exactly.
```

## Phase 8A: Write Tests First (TDD)

### WHERE
File: `tests/cli/commands/test_coordinator.py` (EXTEND EXISTING)

### WHAT
Add test to verify DEFAULT_TEST_COMMAND is used in job parameters.

### Test to Add

```python
class TestExecuteCoordinatorTest:
    """Tests for execute_coordinator_test command function."""
    
    # ... existing tests ...
    
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_uses_default_test_command(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
    ) -> None:
        """Test that DEFAULT_TEST_COMMAND is used in job parameters."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="main")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")
        
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 12345
        
        # Execute
        execute_coordinator_test(args)
        
        # Verify - check that start_job was called with comprehensive test command
        call_args = mock_client.start_job.call_args
        params = call_args[0][1]  # Second positional argument is params dict
        
        # Verify COMMAND parameter exists and contains comprehensive test
        assert "COMMAND" in params
        command = params["COMMAND"]
        
        # Verify comprehensive test script components
        assert "which mcp-coder" in command
        assert "which mcp-code-checker" in command
        assert "which mcp-server-filesystem" in command
        assert "mcp-coder verify" in command
        assert "export MCP_CODER_PROJECT_DIR" in command
        assert "uv sync --extra dev" in command
        assert "which claude" in command
        assert "claude mcp list" in command
        assert "source .venv/bin/activate" in command
```

### Run Test (Should Fail Initially)
```bash
pytest tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_uses_default_test_command -v
```

Expected: Test fails because DEFAULT_TEST_COMMAND doesn't exist yet.

## Phase 8B: Implement Functionality

### WHERE
File: `src/mcp_coder/cli/commands/coordinator.py`

### WHAT
Add module-level constant and update function to use it.

### HOW
Add constant at module level (after imports, before functions)

### Implementation

#### 1. Add Constant After Imports

```python
"""Coordinator CLI command implementation.

This module provides the coordinator test command for triggering
Jenkins-based integration tests for MCP Coder repositories.
"""

import argparse
import logging
import os
import sys
from typing import Optional

from ...utils.jenkins_operations.client import JenkinsClient
from ...utils.jenkins_operations.models import JobStatus
from ...utils.user_config import (
    create_default_config,
    get_config_file_path,
    get_config_value,
)

logger = logging.getLogger(__name__)


# Default test command for coordinator integration tests
# This comprehensive script verifies the complete environment setup
DEFAULT_TEST_COMMAND = """# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra dev
# Claude CLI verification
which claude
claude mcp list
claude -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level debug prompt "What is 1 + 1?"
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
"""


def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    # ... rest of code ...
```

#### 2. Update execute_coordinator_test()

**Find this section (around line 195):**
```python
# Build job parameters
params = {
    "REPO_URL": validated_config["repo_url"],
    "BRANCH_NAME": args.branch_name,
    "COMMAND": "mcp-coder --version",  # OLD - to be replaced
    "GITHUB_CREDENTIALS_ID": validated_config["github_credentials_id"],
}
```

**Replace with:**
```python
# Build job parameters
params = {
    "REPO_URL": validated_config["repo_url"],
    "BRANCH_NAME": args.branch_name,
    "COMMAND": DEFAULT_TEST_COMMAND,  # NEW - comprehensive test script
    "GITHUB_CREDENTIALS_ID": validated_config["github_credentials_id"],
}
```

### ALGORITHM
```
1. Define DEFAULT_TEST_COMMAND as module-level constant
2. In execute_coordinator_test(), use DEFAULT_TEST_COMMAND in params dict
3. Jenkins receives multi-line script as COMMAND parameter
4. Script executes all verification steps in container
```

### DATA

**DEFAULT_TEST_COMMAND**: `str`
- Multi-line shell script
- Contains all environment verification steps
- Used as COMMAND parameter value

**Job Parameters** (updated):
```python
{
    "REPO_URL": str,
    "BRANCH_NAME": str,
    "COMMAND": str,  # Now contains DEFAULT_TEST_COMMAND (multi-line)
    "GITHUB_CREDENTIALS_ID": str,
}
```

## Phase 8C: Verify Implementation

### Run Tests Again
```bash
pytest tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_uses_default_test_command -v
```

Expected: Test now passes

### Run All Coordinator Tests
```bash
pytest tests/cli/commands/test_coordinator.py -v
```

Expected: All tests pass

## Phase 8D: Document Test Command

### WHERE
File: `docs/configuration/CONFIG.md`

### WHAT
Add new section explaining what test command runs.

### Add Section (after "Usage Examples" section)

```markdown
## Test Command

When you trigger a coordinator test, Jenkins executes a comprehensive verification script that validates the entire environment setup. This ensures the containerized environment is properly configured before running actual tests.

### What Gets Tested

The default test command performs the following checks:

#### 1. Tool Verification
- Verifies `mcp-coder` is installed and displays version
- Verifies `mcp-code-checker` is installed
- Verifies `mcp-server-filesystem` is installed
- Runs `mcp-coder verify` to check environment

#### 2. Environment Setup
- Sets `MCP_CODER_PROJECT_DIR=/workspace/repo`
- Sets `MCP_CODER_VENV_DIR=/workspace/.venv`
- Syncs dependencies using `uv sync --extra dev`

#### 3. Claude CLI Verification
- Verifies `claude` CLI is installed
- Lists configured MCP servers with `claude mcp list`
- Tests basic Claude functionality with simple prompt

#### 4. MCP Coder Functionality
- Tests MCP Coder with debug logging
- Verifies prompt command works correctly

#### 5. Virtual Environment
- Activates project virtual environment
- Re-verifies `mcp-coder` from within venv

### Test Command Script

The full test script executed by Jenkins:

```bash
# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra dev
# Claude CLI verification
which claude
claude mcp list
claude -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level debug prompt "What is 1 + 1?"
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
```

### Customization

**Note**: The test command is currently hardcoded in the coordinator implementation. Future versions may support custom test commands per repository via configuration.
```

## Phase 8E: Code Quality Checks

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

All checks must pass.

## Success Criteria

- ✅ DEFAULT_TEST_COMMAND constant added to coordinator.py
- ✅ Constant contains comprehensive multi-line test script
- ✅ execute_coordinator_test() uses DEFAULT_TEST_COMMAND in params
- ✅ New test verifies DEFAULT_TEST_COMMAND usage
- ✅ All existing tests still pass
- ✅ CONFIG.md documents what test command does
- ✅ Pylint: No errors
- ✅ Pytest: All tests pass
- ✅ Mypy: No type errors

## Files Modified

### Modified:
- `src/mcp_coder/cli/commands/coordinator.py`:
  - Add DEFAULT_TEST_COMMAND constant (~20 lines)
  - Update execute_coordinator_test() to use constant (1 line change)
- `tests/cli/commands/test_coordinator.py`:
  - Add test_execute_coordinator_test_uses_default_test_command (~40 lines)
- `docs/configuration/CONFIG.md`:
  - Add "Test Command" section (~60-80 lines)

### Total New/Modified Lines: ~120-150 lines

## Estimated Time
~45-60 minutes (including testing and documentation)

## Next Step
After all checks pass, proceed to **Step 9: Clean Up Test Imports**.
