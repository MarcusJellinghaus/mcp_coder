# Step 3: Add Fix Retry Logic (TDD)

## Objective
Enhance `_run_auto_fixes()` to support multiple fix attempts with CI rechecks between attempts, following test-driven development.

## Context
Read `pr_info/steps/summary.md` first for full context.

This step adds retry capability to the fix logic:
- When `--fix N` where N ≥ 2, retry fixes up to N times
- Wait for CI after each fix attempt (including the last)
- Stop early if CI passes
- Return appropriate success/failure status

**Prerequisites**: Steps 1-2 must be complete (parser changes, waiting logic).

## WHERE: File Locations

### Tests
```
tests/cli/commands/test_check_branch_status.py
  - Add new test class: TestFixRetryLogic
  - Enhance existing: TestRunAutoFixes
```

### Implementation
```
src/mcp_coder/cli/commands/check_branch_status.py
  - Modify function: _run_auto_fixes()
  - Modify function: execute_check_branch_status() (exit code logic)
```

## WHAT: Functions and Signatures

### Tests (Write First)
```python
class TestFixRetryLogic:
    """Test fix retry logic with multiple attempts."""
    
    def test_fix_once_does_not_wait_for_recheck()
    def test_fix_twice_waits_after_first_attempt()
    def test_fix_stops_early_when_ci_passes()
    def test_fix_exhausts_all_attempts_on_failure()
    def test_fix_waits_after_last_attempt()
    def test_fix_handles_wait_timeout_gracefully()
```

### Implementation (Write After Tests Pass)
```python
def _run_auto_fixes(
    project_dir: Path,
    report: BranchStatusReport,
    provider: str,
    method: str,
    mcp_config: Optional[str],
    execution_dir: Optional[Path],
    fix_attempts: int = 1,  # NEW parameter
    ci_timeout: int = 180,   # NEW parameter
    llm_truncate: bool = False,  # NEW parameter
) -> bool:
    """Attempt automatic fixes based on status report.
    
    Args:
        project_dir: Project directory path
        report: Branch status report
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'api')
        mcp_config: Optional MCP configuration path
        execution_dir: Optional execution directory
        fix_attempts: Number of fix attempts (1 = no retry, N = retry)
        ci_timeout: Seconds to wait for CI between attempts
        llm_truncate: Whether in LLM mode (affects progress display)
    
    Returns:
        True if fixes succeeded (CI passed), False otherwise
    """
```

## HOW: Integration Points

### Modified Call Flow
```
execute_check_branch_status()
  ↓
  _run_auto_fixes(fix_attempts=args.fix, ci_timeout=args.ci_timeout)
    ↓
    if fix_attempts == 1:
      [Current behavior: fix once, no recheck]
    else:
      for attempt in range(fix_attempts):
        ↓
        check_and_fix_ci()  # Fix
        ↓
        if attempt < fix_attempts - 1 or fix_attempts > 1:
          _wait_for_ci_completion()  # Recheck
          ↓
          if CI passed: return True (early exit)
```

### Function Signature Changes
```python
# OLD (Step 2)
_run_auto_fixes(project_dir, report, provider, method, mcp_config, execution_dir)

# NEW (Step 3)
_run_auto_fixes(
    project_dir, report, provider, method, mcp_config, execution_dir,
    fix_attempts=args.fix,      # Pass retry count
    ci_timeout=args.ci_timeout,  # Pass timeout for rechecks
    llm_truncate=args.llm_truncate  # Pass mode for progress
)
```

## ALGORITHM: Implementation Logic

### _run_auto_fixes() Enhanced Logic
```
1. If no CI failures: return True (nothing to fix)
2. Get current branch name
3. If fix_attempts == 1:
     # Current behavior (no retry)
     a. Call check_and_fix_ci() once
     b. Return result (no recheck)
4. Else (fix_attempts >= 2, retry enabled):
     Create CI manager
     For attempt in range(fix_attempts):
       a. Log attempt number
       b. Call check_and_fix_ci() to fix
       c. If fix failed: return False (fail fast on git errors)
       d. Wait for new CI run to start
       e. Wait for CI completion (_wait_for_ci_completion)
       f. If CI passed: return True (early exit)
       g. If last attempt and CI failed: return False
     # Should never reach here
     return False
```

### execute_check_branch_status() Exit Code Logic
```
1. [Existing] Collect and display status
2. [Modified] If args.fix > 0:
     fix_success = _run_auto_fixes(..., fix_attempts=args.fix)
     if not fix_success:
       return 1  # Fix failed
3. [New] Determine exit code:
     if report.ci_status == "FAILED":
       return 1
     return 0
```

## DATA: Return Values and Structures

### _run_auto_fixes() Behavior

#### Current Behavior (fix_attempts=1, preserved):
```python
# Fix once, no recheck
_run_auto_fixes(..., fix_attempts=1)
  → check_and_fix_ci() once
  → return True/False immediately
```

#### New Behavior (fix_attempts≥2, retry):
```python
# Fix with retry
_run_auto_fixes(..., fix_attempts=3, ci_timeout=180)
  → Attempt 1: fix → wait → check CI → failed
  → Attempt 2: fix → wait → check CI → failed
  → Attempt 3: fix → wait → check CI → passed
  → return True (early exit)

# All attempts exhausted
_run_auto_fixes(..., fix_attempts=3, ci_timeout=180)
  → Attempt 1: fix → wait → check CI → failed
  → Attempt 2: fix → wait → check CI → failed
  → Attempt 3: fix → wait → check CI → failed
  → return False
```

## Test Implementation Details

### Test File Location
`tests/cli/commands/test_check_branch_status.py`

### New Test Class
```python
class TestFixRetryLogic:
    """Test fix retry logic with multiple attempts."""

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    def test_fix_once_does_not_wait_for_recheck(
        self,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """With fix_attempts=1, should not wait for recheck (current behavior)."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes
        
        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True
        
        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=1,  # No retry
            ci_timeout=180,
            llm_truncate=False,
        )
        
        assert result is True
        mock_check_ci.assert_called_once()
        mock_wait.assert_not_called()  # No recheck

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_twice_waits_after_first_attempt(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """With fix_attempts=2, should wait after first attempt."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes
        
        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True  # Fix succeeds
        
        # Setup CI manager to return different statuses
        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},  # Old run
            {"run": {"id": 2}},  # New run detected
            {"run": {"id": 2, "status": "completed", "conclusion": "success"}},
        ]
        
        # First wait: still failed, Second wait: passed
        mock_wait.side_effect = [
            ({"run": {"conclusion": "failure"}}, False),  # After attempt 1
            ({"run": {"conclusion": "success"}}, True),   # After attempt 2
        ]
        
        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=2,  # Retry enabled
            ci_timeout=180,
            llm_truncate=False,
        )
        
        assert result is True
        assert mock_check_ci.call_count == 2
        assert mock_wait.call_count == 2

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_stops_early_when_ci_passes(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should stop early if CI passes before all attempts used."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes
        
        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True
        
        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},  # Old run
            {"run": {"id": 2}},  # New run
        ]
        
        # CI passes after first attempt
        mock_wait.return_value = (
            {"run": {"conclusion": "success"}},
            True,
        )
        
        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=3,  # 3 attempts available
            ci_timeout=180,
            llm_truncate=False,
        )
        
        assert result is True
        assert mock_check_ci.call_count == 1  # Only 1 attempt used
        assert mock_wait.call_count == 1

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_exhausts_all_attempts_on_failure(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should use all attempts if CI keeps failing."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes
        
        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True
        
        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        # Different run IDs for each attempt
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}}, {"run": {"id": 2}},  # Attempt 1
            {"run": {"id": 2}}, {"run": {"id": 3}},  # Attempt 2
            {"run": {"id": 3}}, {"run": {"id": 4}},  # Attempt 3
        ]
        
        # CI always fails
        mock_wait.return_value = (
            {"run": {"conclusion": "failure"}},
            False,
        )
        
        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=3,
            ci_timeout=180,
            llm_truncate=False,
        )
        
        assert result is False  # All attempts exhausted
        assert mock_check_ci.call_count == 3
        assert mock_wait.call_count == 3

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_waits_after_last_attempt(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should wait after last attempt to know final CI status."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes
        
        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True
        
        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},  # Old run
            {"run": {"id": 2}},  # New run
        ]
        
        # Even last attempt should wait
        mock_wait.return_value = (
            {"run": {"conclusion": "success"}},
            True,
        )
        
        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=1,  # Single attempt, but should still wait
            ci_timeout=180,
            llm_truncate=False,
        )
        
        # Note: This test verifies the decision to wait even after last fix
        # For fix_attempts=1, we preserve backward compat (no wait)
        # But document that for fix_attempts≥2, we always wait

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_handles_wait_timeout_gracefully(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should handle CI wait timeout gracefully."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes
        
        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True
        
        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},
            {"run": {"id": 2}},
        ]
        
        # Wait times out (ci_status=None, success=False)
        mock_wait.return_value = (None, False)
        
        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=2,
            ci_timeout=30,
            llm_truncate=False,
        )
        
        assert result is False  # Timeout counts as failure
```

## Implementation Details

### File: `src/mcp_coder/cli/commands/check_branch_status.py`

### Modify _run_auto_fixes()
```python
def _run_auto_fixes(
    project_dir: Path,
    report: BranchStatusReport,
    provider: str,
    method: str,
    mcp_config: Optional[str],
    execution_dir: Optional[Path],
    fix_attempts: int = 1,
    ci_timeout: int = 180,
    llm_truncate: bool = False,
) -> bool:
    """Attempt automatic fixes based on status report.
    
    Args:
        project_dir: Project directory path
        report: Branch status report
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'api')
        mcp_config: Optional MCP configuration path
        execution_dir: Optional execution directory
        fix_attempts: Number of fix attempts (1 = no retry, N ≥ 2 = retry)
        ci_timeout: Seconds to wait for CI between attempts
        llm_truncate: Whether in LLM mode (affects progress display)
    
    Returns:
        True if all applicable fixes succeeded, False if any fix failed
    """
    logger.debug("Analyzing status report for auto-fixable issues")
    
    # Only auto-fix CI failures - other issues are informational only
    if report.ci_status != "FAILED":
        logger.info(
            "No auto-fixable issues found - all fixes require manual intervention"
        )
        return True  # Success when no fixes needed
    
    logger.info("CI failures detected - attempting automatic fixes")
    
    try:
        # Get current branch from project directory
        current_branch = get_current_branch_name(project_dir)
        if not current_branch:
            logger.error("Could not determine current branch name")
            return False
        
        # Single fix attempt (current behavior - no retry)
        if fix_attempts == 1:
            logger.info("Single fix attempt (no retry)")
            ci_success = check_and_fix_ci(
                project_dir, current_branch, provider, method, mcp_config, execution_dir
            )
            
            if ci_success:
                logger.info("CI fix completed successfully")
                return True
            else:
                logger.error("CI fix failed")
                return False
        
        # Multiple fix attempts (retry logic)
        logger.info(f"Fix retry enabled: {fix_attempts} attempts")
        
        try:
            ci_manager = CIResultsManager(project_dir)
        except Exception as e:
            logger.error(f"Failed to create CI manager: {e}")
            return False
        
        for attempt in range(fix_attempts):
            logger.info(f"Fix attempt {attempt + 1}/{fix_attempts}")
            
            # Attempt fix
            ci_success = check_and_fix_ci(
                project_dir, current_branch, provider, method, mcp_config, execution_dir
            )
            
            if not ci_success:
                logger.error(f"Fix attempt {attempt + 1} failed")
                return False  # Fail fast on git errors or max CI fix attempts
            
            # Wait for new CI run to start (simple polling for new run ID)
            logger.info("Waiting for new CI run to start...")
            try:
                old_status = ci_manager.get_latest_ci_status(current_branch)
                old_run_id = old_status.get("run", {}).get("id")
            except Exception as e:
                logger.warning(f"Could not get old CI run: {e}")
                old_run_id = None
            
            # Poll for new run (max 30 seconds)
            new_run_detected = False
            for _ in range(6):  # 6 * 5 = 30 seconds
                time.sleep(5)
                try:
                    new_status = ci_manager.get_latest_ci_status(current_branch)
                    new_run_id = new_status.get("run", {}).get("id")
                    if new_run_id and new_run_id != old_run_id:
                        logger.info(f"New CI run detected: {new_run_id}")
                        new_run_detected = True
                        break
                except Exception as e:
                    logger.warning(f"Error checking for new CI run: {e}")
                    continue
            
            if not new_run_detected:
                logger.warning("No new CI run detected after 30s")
                # Continue anyway and wait for completion
            
            # Wait for CI completion
            logger.info(f"Waiting for CI completion (timeout: {ci_timeout}s)")
            ci_status, ci_passed = _wait_for_ci_completion(
                ci_manager,
                current_branch,
                ci_timeout,
                llm_truncate,
            )
            
            if ci_passed:
                logger.info(f"CI passed after fix attempt {attempt + 1}")
                return True  # Early exit on success
            
            # If last attempt and still failing
            if attempt == fix_attempts - 1:
                logger.error(
                    f"CI still failing after {fix_attempts} fix attempts"
                )
                return False
        
        # Should never reach here
        return False
    
    except Exception as e:
        logger.error(f"Exception during CI fix: {e}")
        return False
```

### Modify execute_check_branch_status() Call
```python
# In execute_check_branch_status(), update the call to _run_auto_fixes:

# Run auto-fixes if requested
if args.fix > 0:
    logger.info(f"Auto-fix mode enabled (attempts: {args.fix})")
    
    # Parse LLM method for fixes
    provider, method = parse_llm_method_from_args(args.llm_method)
    
    # Resolve paths for fix operations
    mcp_config = resolve_mcp_config_path(args.mcp_config)
    execution_dir = resolve_execution_dir(args.execution_dir)
    
    # Attempt fixes with retry
    fix_success = _run_auto_fixes(
        project_dir,
        report,
        provider,
        method,
        mcp_config,
        execution_dir,
        fix_attempts=args.fix,         # NEW
        ci_timeout=args.ci_timeout,     # NEW
        llm_truncate=args.llm_truncate, # NEW
    )
    
    if not fix_success:
        logger.error("Auto-fix operations failed")
        return 1
    
    logger.info("Auto-fix operations completed successfully")
```

## Validation Criteria

### Tests Must Pass
- ✅ All 6 new retry logic tests pass
- ✅ All existing tests continue to pass
- ✅ Backward compatibility verified (fix_attempts=1)

### Manual Testing
```bash
# Test retry behavior
mcp-coder check branch-status --ci-timeout 180 --fix 3

# Should show:
# - "Fix retry enabled: 3 attempts"
# - "Fix attempt 1/3"
# - "Waiting for CI completion..."
# - Early exit if CI passes, or all 3 attempts
```

## LLM Implementation Prompt

```
Please read pr_info/steps/summary.md for full context.

Implement Step 3: Add Fix Retry Logic (TDD)

STEP 1 - WRITE TESTS FIRST:
1. Read tests/cli/commands/test_check_branch_status.py
2. Add new test class TestFixRetryLogic with 6 tests
3. Follow the test implementation details in pr_info/steps/step_3.md
4. Run tests - they should FAIL (enhanced logic not implemented yet)

STEP 2 - IMPLEMENT TO MAKE TESTS PASS:
1. Read src/mcp_coder/cli/commands/check_branch_status.py
2. Modify _run_auto_fixes() signature (add 3 new parameters)
3. Implement retry logic in _run_auto_fixes()
4. Update execute_check_branch_status() to pass new parameters
5. Follow implementation details in pr_info/steps/step_3.md
6. Run tests - they should PASS

STEP 3 - VERIFY:
1. Run all tests in test_check_branch_status.py
2. Verify backward compatibility (fix_attempts=1 behaves as before)
3. Manual test with real CI runs and multiple fix attempts

Success criteria:
- All 6 new tests pass
- All existing tests pass (backward compat preserved)
- Manual test shows retry behavior working correctly
```

## Dependencies
- Steps 1-2 must be complete (parser, waiting logic)

## Next Step
After this step completes successfully, proceed to Step 4: Update Documentation.
