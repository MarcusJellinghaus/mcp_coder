# Step 5: Remove post-error task tracker display and final verification

## Context
See [summary.md](./summary.md) for full implementation overview.

This step cleans up the post-error progress display and verifies all acceptance criteria.

## WHERE
- `src/mcp_coder/workflows/implement/core.py` — remove duplicate progress display after errors
- `tests/workflows/implement/test_core.py` — verify no post-error progress display

## WHAT

### Remove post-error progress display

In `run_implement_workflow()`, the current code at the error handling section shows:

```python
    if error_occurred:
        logger.log(
            NOTICE,
            f"Workflow stopped due to error after processing {completed_tasks} task(s)",
        )
        if completed_tasks > 0:
            logger.log(NOTICE, "\nProgress before error:")
            log_progress_summary(project_dir)
        return 1
```

This block should be replaced — the failure banner from `_handle_workflow_failure()` (Step 4) already shows progress. The `return 1` should still happen, but the `log_progress_summary` call and surrounding log messages should be removed since `_handle_workflow_failure()` was already called at the point of failure in the task loop.

### After replacement
```python
    if error_occurred:
        return 1
```

The failure details (including progress) are already logged by `_handle_workflow_failure()` at each error exit point.

## TESTS

```python
class TestNoPostErrorProgressDisplay:
    """Verify post-error progress display is removed."""

    @patch("mcp_coder.workflows.implement.core._handle_workflow_failure")
    @patch("mcp_coder.workflows.implement.core.log_progress_summary")
    @patch("mcp_coder.workflows.implement.core.process_single_task")
    # ... (other prerequisite mocks)
    def test_no_progress_summary_after_error(self, ...):
        """After error, log_progress_summary should NOT be called again."""
        # Setup: process_single_task returns error
        mock_process.return_value = (False, "error")
        
        result = run_implement_workflow(Path("/project"), "claude")
        
        assert result == 1
        # log_progress_summary is called once for initial display (Step 3 in workflow)
        # but NOT again after error
        # _handle_workflow_failure should have been called instead
        mock_handle_failure.assert_called_once()
```

## VERIFICATION CHECKLIST

After all 5 steps, verify all acceptance criteria:

- [ ] `WorkflowFailure` dataclass and `FailureCategory` enum implemented (Step 1)
- [ ] Workflow sets `status-06f:implementing-failed` on general failures (Step 4)
- [ ] Workflow sets `status-06f-ci:ci-fix-needed` when CI fix attempts exhausted (Step 4)
- [ ] Workflow sets `status-06f-timeout:llm-timeout` on LLM timeout (Step 4)
- [ ] GitHub comment posted with structured failure details (Step 4)
- [ ] GitHub comment includes `git diff --stat` (Step 4)
- [ ] Failure banner is prominent with stage, message, and task progress (Step 4)
- [ ] Uncommitted changes shown via git diff --stat (Step 4)
- [ ] Post-error task tracker progress display removed (Step 5)
- [ ] `update_labels` parameter removed (Step 3)
- [ ] Prerequisite failures do not change labels (Step 4)

## LLM PROMPT
```
Implement Step 5 of issue #189 (see pr_info/steps/summary.md for context).

Remove the post-error task tracker progress display from `run_implement_workflow()`.
The `if error_occurred:` block should just `return 1` — failure details
are handled by `_handle_workflow_failure()` already.

Write the test first, then implement.
See pr_info/steps/step_5.md for the exact change and verification checklist.
Run all quality checks after changes.
```
