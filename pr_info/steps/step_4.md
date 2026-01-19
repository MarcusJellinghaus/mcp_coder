# Step 4: Integrate CI Check into Workflow

## Overview

Integrate the `check_and_fix_ci()` function into the main `run_implement_workflow()` function, calling it after finalisation.

## LLM Prompt for This Step

```
Implement Step 4 from pr_info/steps/step_4.md.

Reference the summary at pr_info/steps/summary.md for context.

This step integrates the CI check function into the main workflow.
Add the integration call and update tests to verify the integration.
```

---

## Part 1: Add Integration Test

### WHERE
`tests/workflows/implement/test_ci_check.py` (append to existing file)

### WHAT
Add integration test:

```python
class TestWorkflowIntegration:
    """Tests for CI check integration in run_implement_workflow."""

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.get_latest_commit_sha")
    def test_ci_check_called_after_finalisation(
        self,
        mock_get_sha,
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
        """CI check should be called after successful finalisation."""
        from mcp_coder.workflows.implement.core import run_implement_workflow
        
        # Setup mocks for successful workflow
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereqs.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "no_tasks")  # No tasks to process
        mock_finalise.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_get_sha.return_value = "abc123"
        mock_ci_check.return_value = True
        
        result = run_implement_workflow(
            project_dir=Path("/fake/path"),
            provider="claude",
            method="api",
        )
        
        assert result == 0
        mock_ci_check.assert_called_once()

    @patch("mcp_coder.workflows.implement.core.check_and_fix_ci")
    @patch("mcp_coder.workflows.implement.core.run_finalisation")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    @patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    @patch("mcp_coder.workflows.implement.core.get_latest_commit_sha")
    def test_ci_check_failure_returns_exit_code_1(
        self,
        mock_get_sha,
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
        """When CI check returns False, workflow should return exit code 1."""
        from mcp_coder.workflows.implement.core import run_implement_workflow
        
        mock_git_clean.return_value = True
        mock_main_branch.return_value = True
        mock_prereqs.return_value = True
        mock_rebase.return_value = True
        mock_prepare.return_value = True
        mock_process.return_value = (False, "no_tasks")
        mock_finalise.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_get_sha.return_value = "abc123"
        mock_ci_check.return_value = False  # CI check failed
        
        result = run_implement_workflow(
            project_dir=Path("/fake/path"),
            provider="claude",
            method="api",
        )
        
        assert result == 1  # Should fail

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
        mock_ci_check.assert_not_called()  # Should not be called on error
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

1. Add import at top of file:
```python
from mcp_coder.utils.git_operations.commits import get_latest_commit_sha
```

2. Add CI check after finalisation (after Step 5.5, before Step 6):

```python
    # Step 6: Check CI pipeline and auto-fix if needed
    if not error_occurred:
        logger.info("Checking CI pipeline status...")
        current_branch = get_current_branch_name(project_dir)
        expected_sha = get_latest_commit_sha(project_dir)
        
        if current_branch and expected_sha:
            ci_success = check_and_fix_ci(
                project_dir=project_dir,
                branch=current_branch,
                expected_sha=expected_sha,
                provider=provider,
                method=method,
                mcp_config=mcp_config,
                execution_dir=execution_dir,
            )
            if not ci_success:
                logger.error("CI check failed after maximum fix attempts")
                # TODO: Update to failed status label when #272 is implemented
                return 1
        else:
            logger.warning("Could not determine branch or SHA for CI check - skipping")
```

3. Update Step 6 comment to Step 7 (renumber existing step).

### ALGORITHM
```
1. Check if error_occurred is False
2. Get current branch name
3. Get latest commit SHA
4. If both available:
   a. Call check_and_fix_ci()
   b. If returns False → log error, return 1
5. If branch/SHA unavailable → warn, continue
6. Continue to progress summary
```

### DATA

No new data structures. Uses existing:
- `get_current_branch_name()` → str
- `get_latest_commit_sha()` → str
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
