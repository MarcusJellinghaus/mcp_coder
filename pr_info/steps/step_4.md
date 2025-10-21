# Step 4: Create CLI Command Tests (TDD)

## Objective

Create comprehensive tests for the CLI command handler following Test-Driven Development principles. These tests verify argument parsing, error handling, and proper delegation to the workflow module.

## Reference

Review `summary.md` for context and `tests/cli/commands/test_implement.py` for the established test pattern.

## WHERE: File Paths

### New Files
- `tests/cli/commands/test_create_plan.py` - CLI command handler tests

## WHAT: Test Functions

### Test Class: `TestExecuteCreatePlan`

**Test Coverage:**
1. ✅ Successful workflow execution
2. ✅ Error handling (workflow failure)
3. ✅ Keyboard interrupt handling
4. ✅ Project directory resolution
5. ✅ LLM method parsing
6. ✅ Proper delegation to workflow module

### Key Test Functions

```python
def test_execute_create_plan_success()
    """Test successful create-plan command execution."""

def test_execute_create_plan_workflow_failure()
    """Test error handling when workflow returns error code."""

def test_execute_create_plan_keyboard_interrupt()
    """Test graceful handling of user cancellation."""

def test_execute_create_plan_project_dir_resolution()
    """Test project directory is properly resolved."""

def test_execute_create_plan_llm_method_parsing()
    """Test LLM method is correctly parsed."""

def test_execute_create_plan_exception_handling()
    """Test handling of unexpected exceptions."""
```

## HOW: Integration Points

### Imports Required
```python
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.create_plan import execute_create_plan
```

### Mocking Strategy
- Mock `resolve_project_dir()` to avoid file system dependencies
- Mock `parse_llm_method_from_args()` to avoid LLM setup
- Mock `run_create_plan_workflow()` to isolate CLI layer testing

## ALGORITHM: Test Structure

**Each test follows this pattern:**
```python
# 1. Setup - Create mock arguments
args = MagicMock()
args.issue_number = 123
args.project_dir = "/test/path"
args.llm_method = "claude_code_cli"

# 2. Mock dependencies
with patch('resolve_project_dir') as mock_resolve:
    with patch('parse_llm_method_from_args') as mock_parse:
        with patch('run_create_plan_workflow') as mock_workflow:
            # Configure mocks
            mock_resolve.return_value = Path("/test/path")
            mock_parse.return_value = ("claude", "cli")
            mock_workflow.return_value = 0
            
            # 3. Execute - Call function under test
            result = execute_create_plan(args)
            
            # 4. Assert - Verify behavior
            assert result == 0
            mock_workflow.assert_called_once_with(123, Path("/test/path"), "claude", "cli")
```

## DATA: Test Data

### Mock Arguments
```python
args = MagicMock()
args.issue_number: int = 123
args.project_dir: str = "/test/path"
args.llm_method: str = "claude_code_cli"
```

### Expected Return Values
- Success: `0`
- Error: `1`

## Implementation Details

### Complete Test File Content

Create `tests/cli/commands/test_create_plan.py`:

```python
"""Tests for create-plan CLI command handler."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.create_plan import execute_create_plan


class TestExecuteCreatePlan:
    """Test execute_create_plan CLI command handler."""

    @pytest.fixture
    def mock_args(self) -> MagicMock:
        """Create mock command line arguments."""
        args = MagicMock()
        args.issue_number = 123
        args.project_dir = "/test/project"
        args.llm_method = "claude_code_cli"
        return args

    def test_execute_create_plan_success(self, mock_args: MagicMock) -> None:
        """Test successful create-plan command execution."""
        test_project_dir = Path("/test/project")

        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir"
        ) as mock_resolve:
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args"
            ) as mock_parse:
                with patch(
                    "mcp_coder.cli.commands.create_plan.run_create_plan_workflow"
                ) as mock_workflow:
                    # Configure mocks
                    mock_resolve.return_value = test_project_dir
                    mock_parse.return_value = ("claude", "cli")
                    mock_workflow.return_value = 0

                    # Execute
                    result = execute_create_plan(mock_args)

                    # Assert
                    assert result == 0
                    mock_resolve.assert_called_once_with("/test/project")
                    mock_parse.assert_called_once_with("claude_code_cli")
                    mock_workflow.assert_called_once_with(
                        123, test_project_dir, "claude", "cli"
                    )

    def test_execute_create_plan_workflow_failure(self, mock_args: MagicMock) -> None:
        """Test error handling when workflow returns error code."""
        test_project_dir = Path("/test/project")

        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            return_value=test_project_dir,
        ):
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.cli.commands.create_plan.run_create_plan_workflow",
                    return_value=1,
                ):
                    # Execute
                    result = execute_create_plan(mock_args)

                    # Assert
                    assert result == 1

    def test_execute_create_plan_keyboard_interrupt(
        self, mock_args: MagicMock
    ) -> None:
        """Test graceful handling of user cancellation."""
        test_project_dir = Path("/test/project")

        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            return_value=test_project_dir,
        ):
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.cli.commands.create_plan.run_create_plan_workflow",
                    side_effect=KeyboardInterrupt(),
                ):
                    # Execute
                    result = execute_create_plan(mock_args)

                    # Assert
                    assert result == 1

    def test_execute_create_plan_exception_handling(
        self, mock_args: MagicMock
    ) -> None:
        """Test handling of unexpected exceptions."""
        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            side_effect=RuntimeError("Test error"),
        ):
            # Execute
            result = execute_create_plan(mock_args)

            # Assert
            assert result == 1

    def test_execute_create_plan_project_dir_resolution(
        self, mock_args: MagicMock
    ) -> None:
        """Test project directory is properly resolved."""
        test_project_dir = Path("/resolved/path")

        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir"
        ) as mock_resolve:
            mock_resolve.return_value = test_project_dir

            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.cli.commands.create_plan.run_create_plan_workflow",
                    return_value=0,
                ):
                    # Execute
                    execute_create_plan(mock_args)

                    # Assert - verify resolve was called with correct argument
                    mock_resolve.assert_called_once_with("/test/project")

    def test_execute_create_plan_llm_method_parsing(
        self, mock_args: MagicMock
    ) -> None:
        """Test LLM method is correctly parsed."""
        test_project_dir = Path("/test/project")

        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            return_value=test_project_dir,
        ):
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args"
            ) as mock_parse:
                mock_parse.return_value = ("claude", "api")

                with patch(
                    "mcp_coder.cli.commands.create_plan.run_create_plan_workflow",
                    return_value=0,
                ):
                    # Execute
                    execute_create_plan(mock_args)

                    # Assert - verify parse was called correctly
                    mock_parse.assert_called_once_with("claude_code_cli")

    def test_execute_create_plan_with_different_issue_numbers(self) -> None:
        """Test command works with different issue numbers."""
        test_project_dir = Path("/test/project")

        for issue_num in [1, 42, 999, 12345]:
            args = MagicMock()
            args.issue_number = issue_num
            args.project_dir = "/test/project"
            args.llm_method = "claude_code_cli"

            with patch(
                "mcp_coder.cli.commands.create_plan.resolve_project_dir",
                return_value=test_project_dir,
            ):
                with patch(
                    "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
                    return_value=("claude", "cli"),
                ):
                    with patch(
                        "mcp_coder.cli.commands.create_plan.run_create_plan_workflow"
                    ) as mock_workflow:
                        mock_workflow.return_value = 0

                        # Execute
                        result = execute_create_plan(args)

                        # Assert
                        assert result == 0
                        # Verify issue number was passed correctly
                        assert mock_workflow.call_args[0][0] == issue_num
```

## Verification Steps

1. **Run Tests:**
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-v", "tests/cli/commands/test_create_plan.py"]
   )
   ```

2. **Expected Output:**
   ```
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_success PASSED
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_workflow_failure PASSED
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_keyboard_interrupt PASSED
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_exception_handling PASSED
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_project_dir_resolution PASSED
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_llm_method_parsing PASSED
   tests/cli/commands/test_create_plan.py::TestExecuteCreatePlan::test_execute_create_plan_with_different_issue_numbers PASSED
   
   ========== 7 passed ==========
   ```

3. **Code Quality:**
   ```bash
   mcp__code-checker__run_pylint_check(target_directories=["tests/cli/commands"])
   mcp__code-checker__run_mypy_check(target_directories=["tests/cli/commands"])
   ```

## Next Steps

Proceed to **Step 5** to update existing workflow tests with new import paths.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4: Create CLI Command Tests (TDD)

Requirements:
1. Create tests/cli/commands/test_create_plan.py with comprehensive test coverage
2. Follow the pattern from tests/cli/commands/test_implement.py
3. Test all success and error cases
4. Use proper mocking to isolate CLI layer testing
5. Include proper docstrings and type hints

After implementation:
1. Run the tests and verify all pass
2. Check code coverage for the CLI command handler
3. Run pylint and mypy to ensure code quality

The tests should pass immediately since we already implemented the CLI handler in Step 1.

Do not proceed to the next step yet - wait for confirmation.
```
