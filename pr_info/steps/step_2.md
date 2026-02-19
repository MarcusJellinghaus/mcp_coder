# Step 2: Add CI Waiting Logic (TDD)

## Objective
Implement CI polling functionality to wait for CI completion when `--ci-timeout > 0`, following test-driven development.

## Context
Read `pr_info/steps/summary.md` first for full context.

This step adds the ability to wait for CI completion before displaying status:
- Poll every 15 seconds until CI completes or timeout
- Show progress feedback (dots) in human mode
- Silent polling in LLM mode
- Early exit on completion or timeout

**Prerequisites**: Step 1 must be complete (parser changes).

## WHERE: File Locations

### Tests
```
tests/cli/commands/test_check_branch_status.py
  - Add new test class: TestCIWaitingLogic
```

### Implementation
```
src/mcp_coder/cli/commands/check_branch_status.py
  - Add function: _wait_for_ci_completion()
  - Add function: _show_progress()
  - Modify function: execute_check_branch_status()
```

## WHAT: Functions and Signatures

### Tests (Write First)
```python
class TestCIWaitingLogic:
    """Test CI waiting and polling functionality."""
    
    def test_wait_for_ci_timeout_zero_returns_immediately()
    def test_wait_for_ci_polls_until_completion()
    def test_wait_for_ci_respects_timeout()
    def test_wait_for_ci_shows_progress_in_human_mode()
    def test_wait_for_ci_silent_in_llm_mode()
    def test_wait_for_ci_early_exit_on_completion()
    def test_wait_for_ci_handles_api_errors_gracefully()
    def test_execute_with_ci_timeout_waits_before_display()
```

### Implementation (Write After Tests Pass)
```python
def _show_progress(show: bool) -> None:
    """Print a progress dot if show is True.
    
    Args:
        show: Whether to show progress (False in LLM mode)
    """

def _wait_for_ci_completion(
    ci_manager: CIResultsManager,
    branch: str,
    timeout_seconds: int,
    llm_mode: bool,
) -> tuple[Optional[CIStatusData], bool]:
    """Wait for CI completion with timeout.
    
    Args:
        ci_manager: CI results manager instance
        branch: Branch name to check
        timeout_seconds: Maximum seconds to wait
        llm_mode: True to suppress progress output
    
    Returns:
        Tuple of (ci_status, success):
        - ci_status: Latest CI status dict or None
        - success: True if CI passed, False if failed/timeout
    """

def execute_check_branch_status(args: argparse.Namespace) -> int:
    """Execute branch status check command.
    
    Modified to support --ci-timeout parameter.
    """
```

## HOW: Integration Points

### Imports (Add to check_branch_status.py)
```python
import time
from typing import Optional, Tuple
from ...utils.github_operations.ci_results_manager import CIResultsManager, CIStatusData
```

### Call Flow
```
execute_check_branch_status()
  ↓
  if args.ci_timeout > 0:
    _wait_for_ci_completion()  ← NEW
      ↓
      _show_progress()  ← NEW
  ↓
  collect_branch_status()  ← EXISTING
  ↓
  display report  ← EXISTING
```

## ALGORITHM: Implementation Logic

### _show_progress()
```
1. If show is False: return immediately
2. Print "." to stdout without newline
3. Flush stdout for immediate display
```

### _wait_for_ci_completion()
```
1. Calculate max_attempts = timeout_seconds / 15
2. Show initial message (if not llm_mode)
3. For attempt in range(max_attempts):
     a. Get latest CI status from manager
     b. If no run found and last attempt: return (None, True)  # Graceful
     c. If run completed:
        - If conclusion == "success": return (status, True)
        - Else: return (status, False)  # Failed
     d. Show progress dot (if not llm_mode)
     e. Sleep 15 seconds
4. Return (current_status, False)  # Timeout
```

### execute_check_branch_status() Enhancement
```
1. [Existing] Resolve project_dir
2. [NEW] If args.ci_timeout > 0:
     a. Create CIResultsManager
     b. Get current branch name
     c. Call _wait_for_ci_completion()
     d. Handle timeout/error cases
3. [Existing] Collect branch status
4. [Existing] Display report
5. [Existing] Run fixes if requested
6. [Modified] Return appropriate exit code
```

## DATA: Return Values and Structures

### _wait_for_ci_completion() Returns
```python
# CI passed
(CIStatusData{...}, True)

# CI failed
(CIStatusData{...}, False)

# No CI found (graceful exit)
(None, True)

# Timeout (graceful exit)
(CIStatusData{...}, False)

# API error (graceful exit)
(None, True)
```

### Exit Codes from execute_check_branch_status()
```python
0  # Success: CI passed or graceful exit (no CI, API errors)
1  # Failure: CI failed or timeout
2  # Technical error: Invalid arguments, Git errors
```

## Test Implementation Details

### Test File Location
`tests/cli/commands/test_check_branch_status.py`

### New Test Class
```python
class TestCIWaitingLogic:
    """Test CI waiting and polling functionality."""

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_timeout_zero_returns_immediately(
        self, mock_sleep: Mock
    ) -> None:
        """With timeout=0, should return immediately without polling."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        
        # Should not be called with timeout=0
        result = _wait_for_ci_completion(mock_manager, "branch", 0, False)
        
        assert result == (None, True)  # Graceful exit
        mock_sleep.assert_not_called()
        mock_manager.get_latest_ci_status.assert_not_called()

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_polls_until_completion(
        self, mock_sleep: Mock
    ) -> None:
        """Should poll every 15 seconds until CI completes."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        # First call: in progress, Second call: completed
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"status": "in_progress"}, "jobs": []},
            {
                "run": {"status": "completed", "conclusion": "success"},
                "jobs": [],
            },
        ]
        
        ci_status, success = _wait_for_ci_completion(
            mock_manager, "branch", 60, True
        )
        
        assert success is True
        assert ci_status["run"]["conclusion"] == "success"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(15)

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_respects_timeout(
        self, mock_sleep: Mock
    ) -> None:
        """Should respect timeout and return after max attempts."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        # Always return in_progress (never completes)
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "in_progress"},
            "jobs": [],
        }
        
        # 45 second timeout = 3 attempts (45/15)
        ci_status, success = _wait_for_ci_completion(
            mock_manager, "branch", 45, True
        )
        
        assert success is False  # Timeout
        assert mock_sleep.call_count == 3

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_shows_progress_in_human_mode(
        self, mock_sleep: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Should show progress dots in human mode."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"status": "in_progress"}, "jobs": []},
            {
                "run": {"status": "completed", "conclusion": "success"},
                "jobs": [],
            },
        ]
        
        _wait_for_ci_completion(mock_manager, "branch", 30, llm_mode=False)
        
        captured = capsys.readouterr()
        assert "Waiting for CI" in captured.out
        assert "." in captured.out  # Progress dots

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_silent_in_llm_mode(
        self, mock_sleep: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Should be silent in LLM mode."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }
        
        _wait_for_ci_completion(mock_manager, "branch", 30, llm_mode=True)
        
        captured = capsys.readouterr()
        assert captured.out == ""  # No output in LLM mode

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_early_exit_on_completion(
        self, mock_sleep: Mock
    ) -> None:
        """Should exit immediately when CI completes."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        # CI already completed on first check
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }
        
        ci_status, success = _wait_for_ci_completion(
            mock_manager, "branch", 300, True
        )
        
        assert success is True
        assert mock_sleep.call_count == 0  # No waiting needed
        assert mock_manager.get_latest_ci_status.call_count == 1

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_handles_api_errors_gracefully(
        self, mock_sleep: Mock
    ) -> None:
        """Should handle API errors gracefully and return success."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )
        
        mock_manager = Mock()
        mock_manager.get_latest_ci_status.side_effect = Exception("API Error")
        
        ci_status, success = _wait_for_ci_completion(
            mock_manager, "branch", 30, True
        )
        
        assert ci_status is None
        assert success is True  # Graceful exit on API error

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_execute_with_ci_timeout_waits_before_display(
        self,
        mock_collect: Mock,
        mock_wait: Mock,
        mock_branch: Mock,
        mock_ci_manager: Mock,
        mock_resolve: Mock,
        sample_report: BranchStatusReport,
    ) -> None:
        """Test execute_check_branch_status calls wait before display."""
        from mcp_coder.cli.commands.check_branch_status import (
            execute_check_branch_status,
        )
        
        project_dir = Path("/test/project")
        mock_resolve.return_value = project_dir
        mock_branch.return_value = "feature-branch"
        mock_wait.return_value = (
            {"run": {"status": "completed", "conclusion": "success"}},
            True,
        )
        mock_collect.return_value = sample_report
        
        args = argparse.Namespace(
            project_dir="/test/project",
            ci_timeout=180,
            fix=0,
            llm_truncate=False,
        )
        
        result = execute_check_branch_status(args)
        
        assert result == 0
        mock_wait.assert_called_once()
        mock_collect.assert_called_once()
```

## Implementation Details

### File: `src/mcp_coder/cli/commands/check_branch_status.py`

### Add Helper Functions
```python
def _show_progress(show: bool) -> None:
    """Print a progress dot if show is True.
    
    Args:
        show: Whether to show progress (False in LLM mode)
    """
    if not show:
        return
    print(".", end="", flush=True)


def _wait_for_ci_completion(
    ci_manager: CIResultsManager,
    branch: str,
    timeout_seconds: int,
    llm_mode: bool,
) -> tuple[Optional[CIStatusData], bool]:
    """Wait for CI completion with timeout.
    
    Args:
        ci_manager: CI results manager instance
        branch: Branch name to check
        timeout_seconds: Maximum seconds to wait
        llm_mode: True to suppress progress output
    
    Returns:
        Tuple of (ci_status, success):
        - ci_status: Latest CI status dict or None
        - success: True if CI passed, False if failed/timeout
    """
    if timeout_seconds <= 0:
        return None, True  # Graceful exit, no wait requested
    
    show_progress = not llm_mode
    poll_interval = 15  # seconds
    max_attempts = timeout_seconds // poll_interval
    
    if show_progress:
        print(f"Waiting for CI completion (timeout: {timeout_seconds}s)...", end="")
    
    for attempt in range(max_attempts):
        try:
            ci_status = ci_manager.get_latest_ci_status(branch)
        except Exception as e:
            logger.info(f"CI API error during polling: {e}")
            if show_progress:
                print()  # Newline after dots
            return None, True  # Graceful exit on API errors
        
        run_info = ci_status.get("run", {})
        
        # No CI run found yet
        if not run_info:
            if attempt == max_attempts - 1:
                if show_progress:
                    print()
                logger.info("No CI run found within timeout")
                return None, True  # Graceful exit
            _show_progress(show_progress)
            time.sleep(poll_interval)
            continue
        
        # Check if CI completed
        if run_info.get("status") == "completed":
            if show_progress:
                print()  # Newline after dots
            
            conclusion = run_info.get("conclusion")
            if conclusion == "success":
                logger.info("CI passed")
                return ci_status, True
            else:
                logger.info(f"CI completed with conclusion: {conclusion}")
                return ci_status, False
        
        # CI still running, continue polling
        _show_progress(show_progress)
        time.sleep(poll_interval)
    
    # Timeout reached
    if show_progress:
        print()
    logger.info("CI polling timeout reached")
    return ci_status, False
```

### Modify execute_check_branch_status()
```python
def execute_check_branch_status(args: argparse.Namespace) -> int:
    """Execute branch status check command.
    
    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - ci_timeout: Seconds to wait for CI (0 = no wait)
            - fix: Number of fix attempts (0 = no fix)
            - llm_truncate: Whether to use LLM-friendly output format
            - llm_method: LLM method for fixes (if --fix enabled)
            - mcp_config: Optional MCP configuration path
            - execution_dir: Optional execution directory
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting branch status check")
        
        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)
        
        # NEW: Wait for CI completion if timeout specified
        if args.ci_timeout > 0:
            logger.debug(f"CI timeout specified: {args.ci_timeout}s")
            try:
                ci_manager = CIResultsManager(project_dir)
                current_branch = get_current_branch_name(project_dir)
                
                if not current_branch:
                    logger.error("Could not determine current branch")
                    return 2  # Technical error
                
                ci_status, ci_success = _wait_for_ci_completion(
                    ci_manager,
                    current_branch,
                    args.ci_timeout,
                    args.llm_truncate,
                )
                
                # If CI failed after waiting, note for later display
                # (status will be collected again below for full report)
                if not ci_success and ci_status:
                    logger.debug("CI failed after waiting")
            
            except Exception as e:
                logger.warning(f"CI wait failed: {e}")
                # Continue to display current status
        
        # Collect branch status (EXISTING)
        logger.debug("Collecting branch status information")
        report = collect_branch_status(project_dir, args.llm_truncate)
        
        # Display status report (EXISTING)
        output = (
            report.format_for_llm() if args.llm_truncate else report.format_for_human()
        )
        try:
            print(output)
        except UnicodeEncodeError:
            print(output.encode("ascii", errors="replace").decode("ascii"))
        
        # Run auto-fixes if requested (EXISTING - will be enhanced in Step 3)
        if args.fix > 0:
            logger.info(f"Auto-fix mode enabled (attempts: {args.fix})")
            
            # Parse LLM method for fixes
            provider, method = parse_llm_method_from_args(args.llm_method)
            
            # Resolve paths for fix operations
            mcp_config = resolve_mcp_config_path(args.mcp_config)
            execution_dir = resolve_execution_dir(args.execution_dir)
            
            # Attempt fixes (will be enhanced in Step 3)
            fix_success = _run_auto_fixes(
                project_dir, report, provider, method, mcp_config, execution_dir
            )
            
            if not fix_success:
                logger.error("Auto-fix operations failed")
                return 1
            
            logger.info("Auto-fix operations completed successfully")
        
        # NEW: Determine exit code based on CI status
        if report.ci_status == "FAILED":
            return 1  # CI failed
        
        return 0
    
    except Exception as e:
        print(f"Error collecting branch status: {e}", file=sys.stderr)
        logger.error(
            f"Unexpected error in check_branch_status command: {e}", exc_info=True
        )
        return 1
```

## Validation Criteria

### Tests Must Pass
- ✅ All 8 new waiting logic tests pass
- ✅ All existing tests continue to pass

### Manual Testing
```bash
# Test waiting behavior
mcp-coder check branch-status --ci-timeout 30

# Should show:
# - "Waiting for CI completion (timeout: 30s)..." message
# - Progress dots every 15 seconds
# - Final status when complete or timeout
```

## LLM Implementation Prompt

```
Please read pr_info/steps/summary.md for full context.

Implement Step 2: Add CI Waiting Logic (TDD)

STEP 1 - WRITE TESTS FIRST:
1. Read tests/cli/commands/test_check_branch_status.py
2. Add new test class TestCIWaitingLogic with 8 tests
3. Follow the test implementation details in pr_info/steps/step_2.md
4. Run tests - they should FAIL (functions not implemented yet)

STEP 2 - IMPLEMENT TO MAKE TESTS PASS:
1. Read src/mcp_coder/cli/commands/check_branch_status.py
2. Add imports: time, Optional, Tuple, CIResultsManager, CIStatusData
3. Add _show_progress() helper function
4. Add _wait_for_ci_completion() function
5. Modify execute_check_branch_status() to call waiting logic
6. Follow implementation details in pr_info/steps/step_2.md
7. Run tests - they should PASS

STEP 3 - VERIFY:
1. Run all tests in test_check_branch_status.py
2. Verify no regressions (existing tests still pass)
3. Manual test with real CI run

Success criteria:
- All 8 new tests pass
- All existing tests pass
- Manual test shows progress dots and waits for CI
```

## Dependencies
- Step 1 must be complete (parser changes)

## Next Step
After this step completes successfully, proceed to Step 3: Add Fix Retry Logic.
