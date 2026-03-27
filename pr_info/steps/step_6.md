# Step 6: `try/finally` Safety Net + SIGTERM Handler in `run_implement_workflow()`

## Context

See [summary.md](summary.md) for full context. This is the core change — wrapping the workflow in a safety net that catches unexpected exits and SIGTERM signals.

## WHERE

- **Source**: `src/mcp_coder/workflows/implement/core.py` — `run_implement_workflow()` function
- **Tests**: `tests/workflows/implement/test_core.py`

## WHAT

### Changes to `run_implement_workflow()`:

1. Capture `start_time` and `build_url` at the top
2. Track `reached_terminal_state` flag
3. Define SIGTERM handler that calls `_handle_workflow_failure()`
4. Wrap main body in `try/finally`
5. Set `reached_terminal_state = True` before every `return` (both `return 0` and `return 1` after `_handle_workflow_failure()`)
6. In `finally`: if not `reached_terminal_state`, call `_handle_workflow_failure()` and restore signal handler
7. Update all existing `WorkflowFailure(...)` constructions to include `build_url` and `elapsed_time`

### Pseudocode:

```python
def run_implement_workflow(project_dir, provider, mcp_config=None, execution_dir=None) -> int:
    start_time = time.time()
    build_url = os.environ.get("BUILD_URL")
    reached_terminal_state = False
    completed_tasks = 0
    total_tasks = 0
    previous_sigterm_handler = None

    def sigterm_handler(signum, frame):
        nonlocal reached_terminal_state
        if not reached_terminal_state:
            reached_terminal_state = True
            elapsed = time.time() - start_time
            _handle_workflow_failure(
                WorkflowFailure(
                    category=FailureCategory.GENERAL,
                    stage="SIGTERM received",
                    message="Workflow terminated by signal",
                    tasks_completed=completed_tasks,
                    tasks_total=total_tasks,
                    build_url=build_url,
                    elapsed_time=elapsed,
                ),
                project_dir,
            )
        sys.exit(1)

    # Register SIGTERM handler
    try:
        previous_sigterm_handler = signal.signal(signal.SIGTERM, sigterm_handler)
    except (OSError, ValueError):
        logger.debug("Could not register SIGTERM handler")

    try:
        # ... entire existing workflow body ...
        # Every `return 0` and `return 1` preceded by `reached_terminal_state = True`
        # Every WorkflowFailure(...) includes build_url=build_url, elapsed_time=time.time()-start_time
    finally:
        # Restore previous SIGTERM handler
        if previous_sigterm_handler is not None:
            try:
                signal.signal(signal.SIGTERM, previous_sigterm_handler)
            except (OSError, ValueError):
                pass

        # Safety net: handle unexpected exit
        if not reached_terminal_state:
            elapsed = time.time() - start_time
            try:
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=FailureCategory.GENERAL,
                        stage="Unexpected exit",
                        message="Workflow exited without reaching a terminal state",
                        tasks_completed=completed_tasks,
                        tasks_total=total_tasks,
                        build_url=build_url,
                        elapsed_time=elapsed,
                    ),
                    project_dir,
                )
            except Exception:
                logger.error("Safety net failure handling also failed", exc_info=True)
```

### New imports needed:

```python
import os
import signal
import sys
```

## HOW

- Add imports for `os`, `signal`, `sys` at top of `core.py`
- The `try/finally` wraps everything after the signal handler registration
- `reached_terminal_state = True` is set before every `return` statement in the workflow
- Existing `WorkflowFailure(...)` constructions gain `build_url=build_url, elapsed_time=time.time() - start_time`
- The `finally` block's `_handle_workflow_failure()` call is wrapped in its own `try/except` to prevent masking the original exception
- SIGTERM handler uses `nonlocal` to access and set `reached_terminal_state`
- Early returns (pre-requisite checks before `try`) don't need the safety net — they're pre-workflow and don't set the "implementing" label

## ALGORITHM

```
1. Record start_time, build_url, set reached_terminal_state = False
2. Register SIGTERM handler (save previous handler)
3. try: run entire workflow body
4.   Before every return: set reached_terminal_state = True
5. finally: restore SIGTERM handler
6.   If not reached_terminal_state: call _handle_workflow_failure() with safety-net failure
```

## DATA

- `build_url`: `str | None` from `os.environ.get("BUILD_URL")`
- `elapsed_time`: `float` from `time.time() - start_time`
- `reached_terminal_state`: `bool` — tracks if workflow reached a known exit

## IMPORTANT: Scope of try/finally

The `try/finally` should wrap the workflow body **starting from the task tracker preparation** (Step 2 in the workflow). The early prerequisite checks (Steps 1, 1.5) return early with `return 1` and don't set the "implementing" label — they don't need the safety net. This avoids false-positive failure comments when prerequisites fail.

## TESTS

Add to `tests/workflows/implement/test_core.py`:

```python
class TestWorkflowSafetyNet:
    def test_safety_net_fires_on_unexpected_exception(self):
        """Safety net calls _handle_workflow_failure on unexpected exception."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", side_effect=RuntimeError("unexpected")), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch("mcp_coder.workflows.implement.core.signal.signal"):

            result = run_implement_workflow(Path("/fake"), "claude")

            assert result == 1
            mock_handle.assert_called()
            failure = mock_handle.call_args[0][0]
            assert failure.stage == "Unexpected exit"
            assert failure.category == FailureCategory.GENERAL

    def test_safety_net_does_not_fire_on_normal_success(self):
        """Safety net does NOT fire when workflow completes successfully."""
        # Mock entire happy path...
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=True), \
             patch("mcp_coder.workflows.implement.core.log_progress_summary"), \
             patch("mcp_coder.workflows.implement.core.get_step_progress", return_value={}), \
             patch("mcp_coder.workflows.implement.core.process_single_task", return_value=(False, "no_tasks")), \
             patch("mcp_coder.workflows.implement.core.run_finalisation", return_value=True), \
             patch("mcp_coder.workflows.implement.core.get_current_branch_name", return_value="feat-123"), \
             patch("mcp_coder.workflows.implement.core.check_and_fix_ci", return_value=True), \
             patch("mcp_coder.workflows.implement.core.IssueManager"), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch("mcp_coder.workflows.implement.core.signal.signal"):

            result = run_implement_workflow(Path("/fake"), "claude")

            assert result == 0
            # Safety net should not have been called (handled failures may call it, but "Unexpected exit" should not)
            unexpected_calls = [c for c in mock_handle.call_args_list if c[0][0].stage == "Unexpected exit"]
            assert len(unexpected_calls) == 0

    def test_safety_net_does_not_double_handle(self):
        """When workflow already handled a failure, safety net does not fire again."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch("mcp_coder.workflows.implement.core.signal.signal"):

            result = run_implement_workflow(Path("/fake"), "claude")

            assert result == 1
            # Should be called once (for the task tracker failure), not twice
            assert mock_handle.call_count == 1
            assert mock_handle.call_args[0][0].stage == "Task tracker preparation"

    def test_safety_net_includes_build_url_and_elapsed(self):
        """Safety net failure includes build_url and elapsed_time."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", side_effect=RuntimeError("boom")), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch("mcp_coder.workflows.implement.core.signal.signal"), \
             patch.dict(os.environ, {"BUILD_URL": "https://jenkins.example.com/job/1/console"}):

            run_implement_workflow(Path("/fake"), "claude")

            failure = mock_handle.call_args[0][0]
            assert failure.build_url == "https://jenkins.example.com/job/1/console"
            assert failure.elapsed_time is not None
            assert failure.elapsed_time >= 0

    def test_existing_failures_include_build_url_and_elapsed(self):
        """Existing handled failures also include build_url and elapsed_time."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch("mcp_coder.workflows.implement.core.signal.signal"), \
             patch.dict(os.environ, {"BUILD_URL": "https://jenkins.example.com/job/2/console"}):

            run_implement_workflow(Path("/fake"), "claude")

            failure = mock_handle.call_args[0][0]
            assert failure.build_url == "https://jenkins.example.com/job/2/console"
            assert failure.elapsed_time is not None


class TestSigtermHandler:
    def test_sigterm_handler_registered(self):
        """SIGTERM handler is registered at workflow start."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=False), \
             patch("mcp_coder.workflows.implement.core.signal.signal") as mock_signal:

            run_implement_workflow(Path("/fake"), "claude")

            # Check SIGTERM was registered
            sigterm_calls = [c for c in mock_signal.call_args_list if c[0][0] == signal.SIGTERM]
            assert len(sigterm_calls) >= 1

    def test_sigterm_handler_restored_in_finally(self):
        """Previous SIGTERM handler is restored after workflow completes."""
        original_handler = MagicMock()
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure"), \
             patch("mcp_coder.workflows.implement.core.signal.signal", return_value=original_handler) as mock_signal:

            run_implement_workflow(Path("/fake"), "claude")

            # Last signal.signal call should restore the original handler
            final_call = mock_signal.call_args_list[-1]
            assert final_call[0][0] == signal.SIGTERM
            assert final_call[0][1] == original_handler
```

## COMMIT

`feat(core): add try/finally safety net and SIGTERM handler to implement workflow (#598)`

## LLM PROMPT

```
Implement Step 6 from pr_info/steps/step_6.md.
Context: pr_info/steps/summary.md

This is the main safety net change in `src/mcp_coder/workflows/implement/core.py`:

1. Add imports: `os`, `signal`, `sys`
2. In `run_implement_workflow()`:
   - Capture `start_time`, `build_url` from env, `reached_terminal_state = False`
   - Register SIGTERM handler that calls `_handle_workflow_failure()` and exits
   - Wrap workflow body (from task tracker prep onwards) in try/finally
   - Set `reached_terminal_state = True` before every `return`
   - In finally: restore SIGTERM handler, fire safety net if not reached_terminal_state
3. Update all existing `WorkflowFailure(...)` to include `build_url=build_url, elapsed_time=time.time() - start_time`
4. Add tests for: safety net fires on unexpected exception, doesn't fire on success, doesn't double-handle, includes build_url/elapsed_time, SIGTERM handler registered and restored.

IMPORTANT: Early returns before try/finally (prerequisite checks) do NOT need the safety net.
Run all code quality checks.
Commit: "feat(core): add try/finally safety net and SIGTERM handler to implement workflow (#598)"
```
