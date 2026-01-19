# Step 3: Implement Main CI Check Function with Tests (TDD)

## Overview

Implement the main `check_and_fix_ci()` function that orchestrates CI polling, failure analysis, and auto-fix attempts. Follow TDD: write tests first, then implement.

## LLM Prompt for This Step

```
Implement Step 3 from pr_info/steps/step_3.md.

Reference the summary at pr_info/steps/summary.md for context.

This step implements the main check_and_fix_ci function using TDD approach.
Write tests first (with mocks for external dependencies), then implement the function.
```

---

## Part 1: Write Tests First

### WHERE
`tests/workflows/implement/test_ci_check.py` (append to existing file from Step 2)

### WHAT
Add tests for the main function:

```python
from unittest.mock import MagicMock, patch
from pathlib import Path
import time


class TestCheckAndFixCI:
    """Tests for check_and_fix_ci function."""

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_passes_first_check_returns_true(self, mock_sleep, mock_ci_manager):
        """When CI passes on first check, should return True immediately."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci
        
        # Setup mock
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success", "commit_sha": "abc123"},
            "jobs": [{"name": "test", "conclusion": "success"}],
        }
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            expected_sha="abc123",
            provider="claude",
            method="api",
        )
        
        assert result is True
        mock_sleep.assert_not_called()  # No polling needed

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_not_found_warns_and_returns_true(self, mock_sleep, mock_ci_manager):
        """When no CI run found after polling, should warn and return True (exit 0)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci
        
        # Setup mock - always returns empty (no CI run)
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            expected_sha="abc123",
            provider="claude",
            method="api",
        )
        
        assert result is True  # Graceful exit

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_sha_mismatch_warns_and_returns_true(self, mock_sleep, mock_ci_manager):
        """When CI run SHA doesn't match expected, should warn and return True."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci
        
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success", "commit_sha": "different_sha"},
            "jobs": [],
        }
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            expected_sha="abc123",
            provider="claude",
            method="api",
        )
        
        assert result is True  # Continue despite mismatch

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.run_formatters")
    @patch("mcp_coder.workflows.implement.core.commit_changes")
    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_ci_fails_fix_succeeds_returns_true(
        self, mock_sleep, mock_push, mock_commit, mock_format, mock_llm, mock_ci_manager
    ):
        """When CI fails but fix succeeds, should return True."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci
        
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        
        # First call: CI failed, Second call: CI passed
        mock_manager.get_latest_ci_status.side_effect = [
            {
                "run": {"id": 1, "status": "completed", "conclusion": "failure", "commit_sha": "abc123"},
                "jobs": [{"name": "test", "conclusion": "failure"}],
            },
            {
                "run": {"id": 2, "status": "completed", "conclusion": "success", "commit_sha": "def456"},
                "jobs": [{"name": "test", "conclusion": "success"}],
            },
        ]
        mock_manager.get_run_logs.return_value = {"test/1_Run.txt": "Error: test failed"}
        
        mock_llm.return_value = "Analysis complete"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            expected_sha="abc123",
            provider="claude",
            method="api",
        )
        
        assert result is True

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    @patch("mcp_coder.workflows.implement.core.ask_llm")
    @patch("mcp_coder.workflows.implement.core.run_formatters")
    @patch("mcp_coder.workflows.implement.core.commit_changes")
    @patch("mcp_coder.workflows.implement.core.push_changes")
    @patch("mcp_coder.workflows.implement.core.time.sleep")
    def test_max_attempts_exhausted_returns_false(
        self, mock_sleep, mock_push, mock_commit, mock_format, mock_llm, mock_ci_manager
    ):
        """When max fix attempts exhausted, should return False (exit 1)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci
        
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        
        # Always return failed CI
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"id": 1, "status": "completed", "conclusion": "failure", "commit_sha": "abc123"},
            "jobs": [{"name": "test", "conclusion": "failure"}],
        }
        mock_manager.get_run_logs.return_value = {"test/1_Run.txt": "Error"}
        
        mock_llm.return_value = "Analysis/fix response"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            expected_sha="abc123",
            provider="claude",
            method="api",
        )
        
        assert result is False  # Max attempts exhausted

    @patch("mcp_coder.workflows.implement.core.CIResultsManager")
    def test_api_error_returns_true_gracefully(self, mock_ci_manager):
        """When API errors occur, should return True with warning (exit 0)."""
        from mcp_coder.workflows.implement.core import check_and_fix_ci
        
        mock_manager = MagicMock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = Exception("API Error")
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
            expected_sha="abc123",
            provider="claude",
            method="api",
        )
        
        assert result is True  # Graceful handling
```

### HOW
Append to the test file created in Step 2.

---

## Part 2: Implement Main Function

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Add the main `check_and_fix_ci()` function:

```python
def check_and_fix_ci(
    project_dir: Path,
    branch: str,
    expected_sha: str,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Check CI status after finalisation and attempt fixes if needed.
    
    Args:
        project_dir: Path to the project directory
        branch: Branch name to check CI for
        expected_sha: Expected commit SHA (from latest push)
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess
    
    Returns:
        True if CI passes or on API errors (exit 0 scenarios)
        False if max fix attempts exhausted (exit 1 scenario)
    """
    pass  # Implement based on tests
```

### HOW

Add imports at top of file:
```python
import time
from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager
```

Add import for constants:
```python
from .constants import (
    # ... existing imports ...
    CI_MAX_FIX_ATTEMPTS,
    CI_MAX_POLL_ATTEMPTS,
    CI_POLL_INTERVAL_SECONDS,
    LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
)
```

### ALGORITHM
```
1. Initialize CIResultsManager
2. Try to get CI status (handle API errors gracefully → return True)
3. Poll loop: wait for CI completion (max 50 attempts, 15s interval)
   - If no CI run found after timeout → warn, return True
   - If SHA mismatch → warn, continue with available data
4. If CI passed → log "CI passed ✓", return True
5. Fix loop (max 3 attempts):
   a. Get failed jobs summary
   b. Get logs for failed job
   c. Delete temp file (clean slate)
   d. Call LLM for analysis → write to temp file + log to console
   e. Call LLM for fix
   f. Run local checks (use existing mcp_code_checker functions)
   g. Format code
   h. Commit and push
   i. Delete temp file (cleanup)
   j. Poll for new CI run
   k. If CI passes → return True
6. Max attempts exhausted → return False
```

### DATA

**Input:**
- `project_dir`: Path
- `branch`: str  
- `expected_sha`: str
- `provider`: str
- `method`: str
- `mcp_config`: Optional[str]
- `execution_dir`: Optional[Path]

**Output:**
- `bool`: True for exit 0 scenarios, False for exit 1

**Temp file:**
- `pr_info/.ci_problem_description.md`

---

## Verification

1. Run tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. All tests should pass
3. Function should handle all edge cases gracefully
