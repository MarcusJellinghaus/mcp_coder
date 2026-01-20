# Step 3: Implement Main CI Check Function with Tests (TDD)

## Overview

Implement the main `check_and_fix_ci()` function that orchestrates CI polling, failure analysis, and auto-fix attempts. Follow TDD: write tests first, then implement.

**Key design decisions:**
- Polling: get latest CI run on branch, wait for it to complete (prevents picking up old runs)
- Two-phase LLM: analysis writes to temp file, Python reads/deletes/logs it, then fix LLM receives content in prompt
- Quality checks run by LLM in fix prompt (consistent with existing pattern)
- Hybrid error handling: API errors → graceful exit 0, git errors during fix → fail fast exit 1

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
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
        }
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
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
            provider="claude",
            method="api",
        )
        
        assert result is True  # Graceful exit

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
                "run": {"id": 1, "status": "completed", "conclusion": "failure"},
                "jobs": [{
                    "name": "test",
                    "conclusion": "failure",
                    "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
                }],
            },
            {
                "run": {"id": 2, "status": "completed", "conclusion": "success"},
                "jobs": [{"name": "test", "conclusion": "success", "steps": []}],
            },
        ]
        mock_manager.get_run_logs.return_value = {"test/1_Run tests.txt": "Error: test failed"}
        
        mock_llm.return_value = "Analysis complete"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
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
            "run": {"id": 1, "status": "completed", "conclusion": "failure"},
            "jobs": [{
                "name": "test",
                "conclusion": "failure",
                "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
            }],
        }
        mock_manager.get_run_logs.return_value = {"test/1_Run tests.txt": "Error"}
        
        mock_llm.return_value = "Analysis/fix response"
        mock_format.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True
        
        result = check_and_fix_ci(
            project_dir=Path("/fake/path"),
            branch="feature-branch",
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
            provider="claude",
            method="api",
        )
        
        assert result is True  # Graceful handling

    # Note: test_analysis_writes_to_temp_file_then_deleted removed per Decision 11
    # The two-phase LLM flow is implicitly tested by other tests
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
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Check CI status after finalisation and attempt fixes if needed.
    
    Args:
        project_dir: Path to the project directory
        branch: Branch name to check CI for
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
from mcp_coder.utils.git_operations.commits import get_latest_commit_sha
```

Add import for constants:
```python
from .constants import (
    # ... existing imports ...
    CI_MAX_FIX_ATTEMPTS,
    CI_MAX_POLL_ATTEMPTS,
    CI_POLL_INTERVAL_SECONDS,
    LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
    LLM_IMPLEMENTATION_TIMEOUT_SECONDS,  # Reused for CI fix - see Decision 9
)
```

### ALGORITHM
```
1. Initialize CIResultsManager
2. Get and log latest local commit SHA (for debugging)
3. Try to get CI status (handle API errors gracefully → return True)
4. Poll loop: wait for CI completion (max 50 attempts, 15s interval)
   - Get latest CI run on branch
   - If not completed → wait 15s, retry
   - If completed → log CI run commit SHA (for debugging), proceed
   - If no CI run found after timeout → warn, return True
5. If CI passed → log "CI_PASSED: Pipeline succeeded", return True (see Decision 14)
6. Fix loop (max 3 attempts):
   a. Get failed jobs summary (includes step info, log filename construction, and excerpt)
   b. Load analysis prompt from prompts.md, substitute [placeholders]
   c. Call LLM for analysis → writes to temp file
   d. Read temp file content, delete file, log content to console
   e. Load fix prompt from prompts.md, substitute [problem_description]
   f. Call LLM for fix (LLM runs quality checks as part of prompt)
   g. Format code
   h. Commit using 3-level fallback: file → LLM generation → default (see Decision 13)
   i. Push changes (fail fast on git errors → return False)
   j. Poll for new CI run (get latest, wait for completion)
   k. If CI passes → return True
7. Max attempts exhausted → return False
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
