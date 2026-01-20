# Step 4: Integrate CI Check into Workflow

## Overview

Integrate the `check_and_fix_ci()` function into the main `run_implement_workflow()` function, calling it after finalisation.

**Note:** Integration tests are simplified to only verify `check_and_fix_ci()` is called with correct parameters (see Decision 6 in Decisions.md).

## LLM Prompt for This Step

```
Implement Step 4 from pr_info/steps/step_4.md.

Reference the summary at pr_info/steps/summary.md for context.

This step integrates the CI check function into the main workflow.
Add the integration call and update tests to verify the integration.
```

---

## Part 1: Add Simplified Integration Test

### WHERE
`tests/workflows/implement/test_ci_check.py` (append to existing file)

### WHAT
Add simplified integration tests that only verify `check_and_fix_ci()` is called with correct parameters:

```python
class TestWorkflowIntegration:
    """Simplified tests for CI check integration in run_implement_workflow.
    
    These tests only verify that check_and_fix_ci() is called with correct parameters.
    The function's behavior is tested in its own unit tests (TestCheckAndFixCI).
    """

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_ci_check_called_with_correct_parameters(
        self,
        mock_get_branch,
        mock_rebase,
        mock_git_clean,
        mock_main_branch,
        mock_prereqs,
        mock_prepare,
        mock_process,
        mock_finalise,
        mock_ci_check,
    ):
        """CI check should be called with branch name and provider/method."""
        from mcp_coder.workflows.implement.core import run_implement_workflow
        
        # Setup mocks for successful workflow
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereqs.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "no_tasks")
        mock_finalise.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_ci_check.return_value = True
        
        run_implement_workflow(
            project_dir=Path("/fake/path"),
            provider="claude",
            method="api",
        )
        
        # Verify check_and_fix_ci was called with expected parameters
        mock_ci_check.assert_called_once()
        call_kwargs = mock_ci_check.call_args.kwargs
        assert call_kwargs["branch"] == "feature-branch"
        assert call_kwargs["provider"] == "claude"
        assert call_kwargs["method"] == "api"

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    def test_ci_check_not_called_on_error(
        self,
        mock_rebase,
        mock_git_clean,
        mock_main_branch,
        mock_prereqs,
        mock_prepare,
        mock_process,
        mock_finalise,
        mock_ci_check,
    ):
        """CI check should NOT be called if workflow had errors."""
        from mcp_coder.workflows.implement.core import run_implement_workflow
        
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereqs.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "error")  # Error occurred
        
        result = run_implement_workflow(
            project_dir=Path("/fake/path"),
            provider="claude",
            method="api",
        )
        
        assert result == 1
        mock_ci_check.assert_not_called()
```

### HOW
Append to existing test file.

---

## Part 2: Integrate into Workflow

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Add CI check call in `run_implement_workflow()` after finalisation (Step 5.5).

### HOW

1. Add CI check after finalisation (after Step 5.5, before Step 6):

```python
    # Step 6: Check CI pipeline and auto-fix if needed
    if not error_occurred:
        logger.info("Checking CI pipeline status...")
        current_branch = get_current_branch_name(project_dir)
        
        if current_branch:
            ci_success = check_and_fix_ci(
                project_dir=project_dir,
                branch=current_branch,
                provider=provider,
                method=method,
                mcp_config=mcp_config,
                execution_dir=execution_dir,
            )
            if not ci_success:
                logger.error("CI check failed after maximum fix attempts")
                return 1
        else:
            logger.warning("Could not determine branch for CI check - skipping")
```

2. Update Step 6 comment to Step 7 (renumber existing step).

### ALGORITHM
```
1. Check if error_occurred is False
2. Get current branch name
3. If branch available:
   a. Call check_and_fix_ci()
   b. If returns False → log error, return 1
4. If branch unavailable → warn, continue
5. Continue to progress summary
```

### DATA

No new data structures. Uses existing:
- `get_current_branch_name()` → str
- `check_and_fix_ci()` → bool

---

## Verification

1. Run all CI check tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. Run existing workflow tests: `pytest tests/workflows/implement/test_core.py -v`
3. All tests should pass
4. Integration should not break existing functionality

---

## Final Checklist

After completing all steps:

- [ ] Constants added to `constants.py`
- [ ] Prompts added to `prompts.md`
- [ ] `.gitignore` updated
- [ ] Helper functions implemented with tests
- [ ] Main `check_and_fix_ci()` function implemented with tests
- [ ] Workflow integration complete with tests
- [ ] All tests pass: `pytest tests/workflows/implement/ -v`
- [ ] Code quality checks pass: pylint, mypy
