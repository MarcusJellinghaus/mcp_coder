# Step 1: Create CLI Command Interface (TDD)

## Context
See `pr_info/steps/summary.md` for full architectural context.

This step creates the CLI command interface following Test-Driven Development. We write tests first, then implement the `execute_create_pr()` function that will be called by the CLI main entry point.

## Objective
Create CLI command interface for `mcp-coder create-pr` following the exact pattern from `implement` command.

## Test-Driven Approach
1. **RED**: Write failing tests for CLI command
2. **GREEN**: Implement minimal code to pass tests
3. **REFACTOR**: Clean up if needed

---

## Part A: Write Tests First (RED Phase)

### WHERE
**File to create:** `tests/cli/commands/test_create_pr.py`

### WHAT
Test the CLI command interface behavior with various scenarios.

### Test Functions

```python
def test_execute_create_pr_success(tmp_path, mock_workflow):
    """Test successful execution of create-pr command."""

def test_execute_create_pr_with_custom_llm_method(tmp_path, mock_workflow):
    """Test execution with custom LLM method."""

def test_execute_create_pr_workflow_failure(tmp_path, mock_workflow):
    """Test handling of workflow failure (returns 1)."""

def test_execute_create_pr_invalid_project_dir(mock_workflow):
    """Test handling of invalid project directory."""

def test_execute_create_pr_keyboard_interrupt(tmp_path, mock_workflow):
    """Test graceful handling of keyboard interrupt."""

def test_execute_create_pr_unexpected_error(tmp_path, mock_workflow):
    """Test handling of unexpected errors."""
```

### TEST IMPLEMENTATION

```python
"""Tests for create-pr CLI command."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.create_pr import execute_create_pr


class TestExecuteCreatePr:
    """Test suite for execute_create_pr CLI command."""

    @pytest.fixture
    def mock_workflow(self):
        """Mock the workflow function."""
        with patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow") as mock:
            mock.return_value = 0  # Success by default
            yield mock

    @pytest.fixture
    def mock_resolve_dir(self):
        """Mock resolve_project_dir utility."""
        with patch("mcp_coder.cli.commands.create_pr.resolve_project_dir") as mock:
            yield mock

    @pytest.fixture
    def mock_parse_llm(self):
        """Mock parse_llm_method_from_args utility."""
        with patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args") as mock:
            mock.return_value = ("claude", "cli")
            yield mock

    def test_execute_create_pr_success(self, tmp_path, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test successful execution of create-pr command."""
        # Setup
        mock_resolve_dir.return_value = tmp_path
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            llm_method="claude_code_cli"
        )

        # Execute
        exit_code = execute_create_pr(args)

        # Verify
        assert exit_code == 0
        mock_resolve_dir.assert_called_once_with(str(tmp_path))
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_workflow.assert_called_once_with(tmp_path, "claude", "cli")

    def test_execute_create_pr_with_custom_llm_method(self, tmp_path, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test execution with custom LLM method."""
        mock_resolve_dir.return_value = tmp_path
        mock_parse_llm.return_value = ("claude", "api")
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            llm_method="claude_code_api"
        )

        exit_code = execute_create_pr(args)

        assert exit_code == 0
        mock_parse_llm.assert_called_once_with("claude_code_api")
        mock_workflow.assert_called_once_with(tmp_path, "claude", "api")

    def test_execute_create_pr_workflow_failure(self, tmp_path, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test handling of workflow failure (returns 1)."""
        mock_resolve_dir.return_value = tmp_path
        mock_workflow.return_value = 1  # Workflow failure
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            llm_method="claude_code_cli"
        )

        exit_code = execute_create_pr(args)

        assert exit_code == 1

    def test_execute_create_pr_invalid_project_dir(self, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test handling of invalid project directory."""
        from sys import exit as sys_exit
        mock_resolve_dir.side_effect = SystemExit(1)  # resolve_project_dir exits on error
        args = argparse.Namespace(
            project_dir="/invalid/path",
            llm_method="claude_code_cli"
        )

        with pytest.raises(SystemExit) as exc_info:
            execute_create_pr(args)
        
        assert exc_info.value.code == 1
        mock_workflow.assert_not_called()

    def test_execute_create_pr_none_project_dir(self, tmp_path, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test with None project_dir (uses current directory)."""
        mock_resolve_dir.return_value = tmp_path
        args = argparse.Namespace(
            project_dir=None,  # Should use current directory
            llm_method="claude_code_cli"
        )

        exit_code = execute_create_pr(args)

        assert exit_code == 0
        mock_resolve_dir.assert_called_once_with(None)

    def test_execute_create_pr_keyboard_interrupt(self, tmp_path, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test graceful handling of keyboard interrupt."""
        mock_resolve_dir.return_value = tmp_path
        mock_workflow.side_effect = KeyboardInterrupt()
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            llm_method="claude_code_cli"
        )

        exit_code = execute_create_pr(args)

        assert exit_code == 1

    def test_execute_create_pr_unexpected_error(self, tmp_path, mock_workflow, mock_resolve_dir, mock_parse_llm):
        """Test handling of unexpected errors."""
        mock_resolve_dir.return_value = tmp_path
        mock_workflow.side_effect = RuntimeError("Unexpected error")
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            llm_method="claude_code_cli"
        )

        exit_code = execute_create_pr(args)

        assert exit_code == 1
```

### HOW TO RUN TESTS (Should FAIL initially)
```bash
# Run just this test file
pytest tests/cli/commands/test_create_pr.py -v

# Expected: All tests FAIL (module not found)
```

---

## Part B: Implement CLI Command (GREEN Phase)

### WHERE
**File to create:** `src/mcp_coder/cli/commands/create_pr.py`

### WHAT - Main Function Signature

```python
def execute_create_pr(args: argparse.Namespace) -> int:
    """
    Execute the create-pr workflow command.
    
    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - llm_method: LLM method ('claude_code_cli' or 'claude_code_api')
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

### HOW - Integration Points

**Imports:**
```python
import argparse
import logging
import sys
from pathlib import Path

from ...workflows.create_pr.core import run_create_pr_workflow
from ...workflows.utils import resolve_project_dir
from ..utils import parse_llm_method_from_args
```

**Logger:**
```python
logger = logging.getLogger(__name__)
```

### ALGORITHM - Core Logic (Pseudocode)

```python
1. Log command start
2. Resolve and validate project directory using shared utility
3. Parse LLM method into (provider, method) tuple
4. Call workflow with validated parameters
5. Return exit code from workflow
6. Handle KeyboardInterrupt → return 1
7. Handle unexpected exceptions → log error, return 1
```

### FULL IMPLEMENTATION

```python
"""Create PR command implementation.

This module provides the CLI command interface for the create-pr workflow,
which generates PR summaries and cleans up repository state.
"""

import argparse
import logging
import sys
from pathlib import Path

from ...workflows.create_pr.core import run_create_pr_workflow
from ...workflows.utils import resolve_project_dir
from ..utils import parse_llm_method_from_args

logger = logging.getLogger(__name__)


def execute_create_pr(args: argparse.Namespace) -> int:
    """Execute the create-pr workflow command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude_code_cli' or 'claude_code_api')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting create-pr command execution")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Parse LLM method using shared utility
        provider, method = parse_llm_method_from_args(args.llm_method)

        # Run the create-pr workflow
        return run_create_pr_workflow(project_dir, provider, method)

    except KeyboardInterrupt:
        print("Operation cancelled by user.")
        return 1

    except Exception as e:
        print(f"Error during workflow execution: {e}", file=sys.stderr)
        logger.error(f"Unexpected error in create-pr command: {e}", exc_info=True)
        return 1
```

### DATA - Return Values

```python
# Success: return 0
# Error: return 1
# Matches pattern from execute_implement()
```

### VALIDATION

Run tests to verify implementation:
```bash
# Should now PASS
pytest tests/cli/commands/test_create_pr.py -v
```

---

## LLM Prompt for This Step

```
I'm implementing Step 1 of the create_PR to CLI command conversion (Issue #139).

Context: Read pr_info/steps/summary.md for full architectural overview.

Task: Create CLI command interface following TDD approach.

Step 1 Details: Read pr_info/steps/step_1.md

Instructions:
1. First, create tests/cli/commands/test_create_pr.py with comprehensive tests
2. Run tests (they should FAIL - RED phase)
3. Create src/mcp_coder/cli/commands/create_pr.py following the exact pattern from implement.py
4. Run tests again (they should PASS - GREEN phase)
5. Run code quality checks (pylint, mypy on new files)

Reference implementation: src/mcp_coder/cli/commands/implement.py

Do NOT modify any other files in this step. Focus only on creating the CLI command interface.
```

---

## Verification Checklist

- [ ] Tests created: `tests/cli/commands/test_create_pr.py`
- [ ] Tests initially fail (RED phase confirmed)
- [ ] Implementation created: `src/mcp_coder/cli/commands/create_pr.py`
- [ ] All tests pass (GREEN phase confirmed)
- [ ] Pylint check passes on new files
- [ ] Mypy check passes on new files
- [ ] Code follows exact pattern from `implement.py`

## Dependencies

### Required Before This Step
- ✅ `src/mcp_coder/cli/commands/implement.py` exists (reference pattern)
- ✅ `src/mcp_coder/workflows/utils.py` exists (shared utilities)
- ✅ `src/mcp_coder/cli/utils.py` exists (shared utilities)

### Blocks
- Step 2 (workflow core needs this CLI interface to exist)

## Notes

- This step creates ONLY the CLI interface, not the workflow logic
- Workflow function `run_create_pr_workflow()` will be created in Step 2
- Tests mock the workflow function to test CLI interface in isolation
- Follows exact same pattern as `execute_implement()` for consistency
