# Step 5: Add Heartbeat Support to `execute_subprocess()` and Pass from `ask_claude_code_cli()`

## Context

See [summary.md](summary.md) for full context. This step adds optional heartbeat logging to `execute_subprocess()` using a daemon thread, and makes `ask_claude_code_cli()` opt in with a 2-minute interval. These were previously two separate steps but are merged since the CLI pass-through is trivially small.

## WHERE

- **Source**: `src/mcp_coder/utils/subprocess_runner.py` — `execute_subprocess()` function
- **Source**: `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — `ask_claude_code_cli()` function
- **Tests**: `tests/utils/test_subprocess_runner.py`
- **Tests**: `tests/llm/providers/claude/test_claude_code_cli.py`

## WHAT

### Part A: Heartbeat in `execute_subprocess()`

Add two optional parameters to `execute_subprocess()`:

```python
def execute_subprocess(
    command: list[str],
    options: CommandOptions | None = None,
    heartbeat_interval_seconds: int | None = None,  # NEW
    heartbeat_message: str = "",                      # NEW
) -> CommandResult:
```

When `heartbeat_interval_seconds` is set and > 0, start a daemon thread before `_run_subprocess()` that logs periodically. Cancel it in `finally`.

### Heartbeat thread implementation:

```python
import threading

def _run_heartbeat(
    stop_event: threading.Event,
    interval: int,
    message: str,
    start_time: float,
) -> None:
    """Heartbeat loop — runs in a daemon thread, logs at regular intervals."""
    while not stop_event.wait(interval):
        elapsed = time.time() - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        logger.info("%s (elapsed: %dm %ds)", message, minutes, seconds)
```

### Integration in `execute_subprocess()` (pseudocode):

```python
def execute_subprocess(command, options=None, heartbeat_interval_seconds=None, heartbeat_message=""):
    # ... existing setup ...

    stop_event = None
    heartbeat_thread = None

    if heartbeat_interval_seconds and heartbeat_interval_seconds > 0:
        stop_event = threading.Event()
        heartbeat_thread = threading.Thread(
            target=_run_heartbeat,
            args=(stop_event, heartbeat_interval_seconds, heartbeat_message, start_time),
            daemon=True,
        )
        heartbeat_thread.start()

    try:
        # ... existing _run_subprocess() call and result handling ...
    finally:
        if stop_event is not None:
            stop_event.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=2)
```

### Part B: Pass heartbeat params from `ask_claude_code_cli()`

```python
# In claude_code_cli.py:
LLM_HEARTBEAT_INTERVAL_SECONDS = 120  # 2 minutes

# Update the execute_subprocess() call:
result = execute_subprocess(
    command,
    options,
    heartbeat_interval_seconds=LLM_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_message="LLM call in progress",
)
```

## HOW

- Add `import threading` at top of `subprocess_runner.py`
- Add `_run_heartbeat()` as a private module-level function
- Modify `execute_subprocess()` to optionally start/stop the heartbeat thread
- Add `LLM_HEARTBEAT_INTERVAL_SECONDS = 120` constant to `claude_code_cli.py`
- Update the `execute_subprocess()` call in `ask_claude_code_cli()` to pass heartbeat params
- Additive change — existing callers pass no heartbeat params and get identical behavior

## TESTS

### Part A tests — `tests/utils/test_subprocess_runner.py`:

```python
class TestHeartbeat:
    def test_no_heartbeat_by_default(self, caplog):
        """No heartbeat logs when params not provided."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(args=["echo"], returncode=0, stdout="", stderr="")
            with caplog.at_level(logging.INFO, logger="mcp_coder.utils.subprocess_runner"):
                execute_subprocess(["echo", "hi"])
            # No heartbeat-related log messages should appear
            heartbeat_logs = [r for r in caplog.records if "heartbeat" in r.message.lower() or "elapsed" in r.message.lower()]
            assert len(heartbeat_logs) == 0

    def test_heartbeat_thread_started_and_stopped(self):
        """Heartbeat thread is started before subprocess and stopped after."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(args=["echo"], returncode=0, stdout="", stderr="")
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                mock_event = MagicMock()
                mock_threading.Event.return_value = mock_event
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread

                execute_subprocess(
                    ["echo", "hi"],
                    heartbeat_interval_seconds=120,
                    heartbeat_message="Test heartbeat",
                )

                mock_threading.Thread.assert_called_once()
                mock_thread.start.assert_called_once()
                mock_event.set.assert_called_once()  # Stop signal sent
                mock_thread.join.assert_called_once()

    def test_heartbeat_stopped_on_exception(self):
        """Heartbeat thread is stopped even if subprocess raises."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.side_effect = TimeoutExpired(["cmd"], 10)
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                mock_event = MagicMock()
                mock_threading.Event.return_value = mock_event
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread

                result = execute_subprocess(
                    ["cmd"], heartbeat_interval_seconds=60, heartbeat_message="test",
                )

                assert result.timed_out is True
                mock_event.set.assert_called_once()  # Stopped despite exception

    def test_heartbeat_zero_interval_disabled(self):
        """heartbeat_interval_seconds=0 does not start a thread."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(args=["echo"], returncode=0, stdout="", stderr="")
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                execute_subprocess(["echo"], heartbeat_interval_seconds=0, heartbeat_message="x")
                mock_threading.Thread.assert_not_called()

    def test_run_heartbeat_logs_periodically(self, caplog):
        """_run_heartbeat logs at intervals until stop event is set."""
        from mcp_coder.utils.subprocess_runner import _run_heartbeat

        stop_event = MagicMock(spec=threading.Event)
        # First wait returns False (not stopped, triggers log), second returns True (stopped, exits)
        stop_event.wait.side_effect = [False, True]

        with caplog.at_level(logging.INFO, logger="mcp_coder.utils.subprocess_runner"):
            _run_heartbeat(stop_event, interval=120, message="Test HB", start_time=time.time())

        assert any("Test HB" in record.message for record in caplog.records)
```

### Part B tests — `tests/llm/providers/claude/test_claude_code_cli.py`:

```python
class TestAskClaudeCodeCliHeartbeat:
    def test_passes_heartbeat_params_to_execute_subprocess(self):
        """Verify heartbeat parameters are passed to execute_subprocess."""
        with patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable") as mock_find:
            mock_find.return_value = "claude"
            with patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess") as mock_exec:
                mock_exec.return_value = CommandResult(
                    return_code=0, stdout=make_valid_stream_output(), stderr="",
                    timed_out=False, command=["claude"], runner_type="subprocess",
                )
                with patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path"):
                    ask_claude_code_cli("test question", timeout=30)

                assert mock_exec.call_args.kwargs["heartbeat_interval_seconds"] == 120
                assert "LLM call in progress" in mock_exec.call_args.kwargs["heartbeat_message"]
```

## COMMIT

`feat(subprocess): add heartbeat logging to execute_subprocess and enable for LLM calls (#598)`

## LLM PROMPT

```
Implement Step 5 from pr_info/steps/step_5.md.
Context: pr_info/steps/summary.md

Part A — Heartbeat in execute_subprocess:
1. Add `_run_heartbeat(stop_event, interval, message, start_time)` function to `src/mcp_coder/utils/subprocess_runner.py`.
2. Add `heartbeat_interval_seconds: int | None = None` and `heartbeat_message: str = ""` parameters to `execute_subprocess()`.
3. Start a daemon thread before `_run_subprocess()` when heartbeat is enabled, stop it in `finally`.
4. Add tests in `tests/utils/test_subprocess_runner.py`.

Part B — Pass heartbeat from ask_claude_code_cli:
1. Add `LLM_HEARTBEAT_INTERVAL_SECONDS = 120` constant to `src/mcp_coder/llm/providers/claude/claude_code_cli.py`.
2. Update the `execute_subprocess()` call in `ask_claude_code_cli()` to pass heartbeat params.
3. Add test in `tests/llm/providers/claude/test_claude_code_cli.py`.

Additive change — existing callers are unaffected. Run all code quality checks.
Commit: "feat(subprocess): add heartbeat logging to execute_subprocess and enable for LLM calls (#598)"
```
