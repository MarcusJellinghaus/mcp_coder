# Step 4: Add `try/finally` Safety Net + SIGTERM Handler

## Context

See [summary.md](summary.md) for full context. This step wraps the workflow in a safety net that catches unexpected exits and SIGTERM signals.

## WHERE

- **Source**: `src/mcp_coder/workflows/implement/core.py` — `run_implement_workflow()` function
- **Tests**: `tests/workflows/implement/test_core.py`

## WHAT

### Changes to `run_implement_workflow()`:

1. Track `reached_terminal_state` flag
2. Define SIGTERM handler that sets a flag and calls `sys.exit(1)`
3. Wrap main body in `try/finally`
4. Set `reached_terminal_state = True` before every `return` (both `return 0` and `return 1` after `_handle_workflow_failure()`)
5. In `finally`: if not `reached_terminal_state`, call `_handle_workflow_failure()` and restore signal handler
6. The `finally` block checks `sigterm_received` flag and handles it from normal context

### Pseudocode:

```python
def run_implement_workflow(project_dir, provider, mcp_config=None, execution_dir=None) -> int:
    start_time = time.time()          # from Step 3
    build_url = os.environ.get("BUILD_URL")  # from Step 3
    reached_terminal_state = False
    sigterm_received = False
    completed_tasks = 0
    total_tasks = 0
    previous_sigterm_handler = None

    def sigterm_handler(signum, frame):
        nonlocal sigterm_received
        sigterm_received = True
        sys.exit(1)

    # Register SIGTERM handler
    try:
        previous_sigterm_handler = signal.signal(signal.SIGTERM, sigterm_handler)
    except (OSError, ValueError):
        logger.debug("Could not register SIGTERM handler")

    try:
        # ... entire existing workflow body ...
        # Every `return 0` and `return 1` preceded by `reached_terminal_state = True`
    finally:
        # Restore previous SIGTERM handler
        if previous_sigterm_handler is not None:
            try:
                signal.signal(signal.SIGTERM, previous_sigterm_handler)
            except (OSError, ValueError):
                pass

        # Safety net: handle unexpected exit (including SIGTERM via sys.exit)
        if not reached_terminal_state:
            elapsed = time.time() - start_time
            stage = "SIGTERM received" if sigterm_received else "Unexpected exit"
            message = "Workflow terminated by signal" if sigterm_received else "Workflow exited without reaching a terminal state"
            try:
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=FailureCategory.GENERAL,
                        stage=stage,
                        message=message,
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
import signal
import sys
```

## HOW

- Add imports for `signal`, `sys` at top of `core.py`
- The SIGTERM handler only sets a flag and calls `sys.exit(1)` — NO I/O inside the signal handler (avoids re-entrancy/deadlock risk)
- The `finally` block runs on `sys.exit()` and checks `sigterm_received` to call `_handle_workflow_failure()` from normal context
- `reached_terminal_state = True` is set before every `return` statement in the workflow
- The `finally` block's `_handle_workflow_failure()` call is wrapped in its own `try/except`
- Early returns (pre-requisite checks before `try`) don't need the safety net

## ALGORITHM

```
1. Set reached_terminal_state = False, sigterm_received = False
2. Register SIGTERM handler that sets sigterm_received = True and calls sys.exit(1)
3. try: run entire workflow body
4.   Before every return: set reached_terminal_state = True
5. finally: restore SIGTERM handler
6.   If not reached_terminal_state:
       - Check sigterm_received flag to determine stage/message
       - Call _handle_workflow_failure() from normal (non-signal) context
```

## IMPORTANT: Scope of try/finally

The `try/finally` should wrap the workflow body **starting from the task tracker preparation**. The early prerequisite checks return early with `return 1` and don't set the "implementing" label — they don't need the safety net.

## IMPORTANT: SIGTERM handler approach

The SIGTERM handler does NOT do I/O directly. It only sets a flag and calls `sys.exit(1)`. The `finally` block (which runs on `sys.exit`) checks the flag and calls `_handle_workflow_failure()` from normal context. This avoids I/O inside signal handlers (re-entrancy/deadlock risk).

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


class TestSigtermHandler:
    def test_sigterm_handler_registered(self):
        """SIGTERM handler is registered at workflow start."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=False), \
             patch("mcp_coder.workflows.implement.core.signal.signal") as mock_signal:

            run_implement_workflow(Path("/fake"), "claude")

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

            final_call = mock_signal.call_args_list[-1]
            assert final_call[0][0] == signal.SIGTERM
            assert final_call[0][1] == original_handler

    def test_sigterm_sets_flag_and_exits(self):
        """SIGTERM handler sets sigterm_received flag and calls sys.exit(1)."""
        # This tests the handler behavior: it should NOT do I/O directly.
        # Instead it sets a flag and calls sys.exit(1), letting the finally
        # block handle failure reporting from normal context.
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker") as mock_prep, \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch("mcp_coder.workflows.implement.core.signal.signal") as mock_signal:

            # Capture the registered handler
            handlers = {}
            def capture_handler(sig, handler):
                handlers[sig] = handler
                return signal.SIG_DFL
            mock_signal.side_effect = capture_handler

            # Make prepare_task_tracker call the SIGTERM handler
            def trigger_sigterm(*args, **kwargs):
                handler = handlers.get(signal.SIGTERM)
                if handler:
                    with pytest.raises(SystemExit):
                        handler(signal.SIGTERM, None)
                raise SystemExit(1)
            mock_prep.side_effect = trigger_sigterm

            with pytest.raises(SystemExit):
                run_implement_workflow(Path("/fake"), "claude")

            # The finally block should have called _handle_workflow_failure
            # with stage "SIGTERM received"
            mock_handle.assert_called()
            failure = mock_handle.call_args[0][0]
            assert failure.stage == "SIGTERM received"
            assert failure.message == "Workflow terminated by signal"
```

## COMMIT

`feat(core): add try/finally safety net and SIGTERM handler to implement workflow (#598)`

## LLM PROMPT

```
Implement Step 4 from pr_info/steps/step_4.md.
Context: pr_info/steps/summary.md

Add the safety net and SIGTERM handler to `src/mcp_coder/workflows/implement/core.py`:

1. Add imports: `signal`, `sys`
2. In `run_implement_workflow()`:
   - Add `reached_terminal_state = False` and `sigterm_received = False`
   - Register SIGTERM handler that ONLY sets `sigterm_received = True` and calls `sys.exit(1)` — NO I/O in the handler
   - Wrap workflow body (from task tracker prep onwards) in try/finally
   - Set `reached_terminal_state = True` before every `return`
   - In finally: restore SIGTERM handler, check `sigterm_received` flag, fire safety net if not reached_terminal_state

IMPORTANT: The SIGTERM handler must NOT do I/O directly. It sets a flag and calls sys.exit(1).
The finally block (which runs on sys.exit) checks the flag and calls _handle_workflow_failure()
from normal context. This avoids re-entrancy/deadlock risk in signal handlers.

3. Add tests for: safety net fires on unexpected exception, doesn't fire on success,
   doesn't double-handle, includes build_url/elapsed_time, SIGTERM handler registered/restored,
   SIGTERM sets flag and exits.

IMPORTANT: Early returns before try/finally (prerequisite checks) do NOT need the safety net.
Run all code quality checks.
Commit: "feat(core): add try/finally safety net and SIGTERM handler to implement workflow (#598)"
```
