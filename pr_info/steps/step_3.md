# Step 3: Add Heartbeat Support to `execute_subprocess()`

## Context

See [summary.md](summary.md) for full context. This step adds optional heartbeat logging to `execute_subprocess()` using a daemon thread, so long-running subprocesses (like LLM calls) emit periodic log messages.

## WHERE

- **Source**: `src/mcp_coder/utils/subprocess_runner.py` — `execute_subprocess()` function
- **Tests**: `tests/utils/test_subprocess_runner.py`

## WHAT

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

## HOW

- Add `import threading` at top of `subprocess_runner.py`
- Add `_run_heartbeat()` as a private module-level function
- Modify `execute_subprocess()` to optionally start/stop the heartbeat thread
- Additive change — existing callers pass no heartbeat params and get identical behavior
- Daemon thread ensures no orphaned threads on process exit

## DATA

- `heartbeat_interval_seconds`: `None` (disabled) or positive int (e.g., `120` for 2 minutes)
- `heartbeat_message`: Caller-defined prefix string, e.g. `"LLM call in progress"`
- Log output: `"LLM call in progress (elapsed: 2m 0s)"`

## TESTS

Add to `tests/utils/test_subprocess_runner.py`:

```python
class TestHeartbeat:
    def test_no_heartbeat_by_default(self):
        """No heartbeat thread started when params not provided."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(args=["echo"], returncode=0, stdout="", stderr="")
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                result = execute_subprocess(["echo", "hi"])
                mock_threading.Thread.assert_not_called()

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

        stop_event = threading.Event()
        # Set the stop event after a brief delay so the loop runs at least once
        # Use a very short interval for testing
        import threading as real_threading

        def stop_after_delay():
            time.sleep(0.15)
            stop_event.set()

        stopper = real_threading.Thread(target=stop_after_delay)
        stopper.start()

        with caplog.at_level(logging.INFO, logger="mcp_coder.utils.subprocess_runner"):
            _run_heartbeat(stop_event, interval=0.05, message="Test HB", start_time=time.time())

        stopper.join()
        assert any("Test HB" in record.message for record in caplog.records)
```

## COMMIT

`feat(subprocess): add optional heartbeat logging to execute_subprocess (#598)`

## LLM PROMPT

```
Implement Step 3 from pr_info/steps/step_3.md.
Context: pr_info/steps/summary.md

1. Add `_run_heartbeat(stop_event, interval, message, start_time)` function to `src/mcp_coder/utils/subprocess_runner.py`.
2. Add `heartbeat_interval_seconds: int | None = None` and `heartbeat_message: str = ""` parameters to `execute_subprocess()`.
3. Start a daemon thread before `_run_subprocess()` when heartbeat is enabled, stop it in `finally`.
4. Add tests in `tests/utils/test_subprocess_runner.py`.

This is an additive change — existing callers are unaffected. Run all code quality checks.
Commit: "feat(subprocess): add optional heartbeat logging to execute_subprocess (#598)"
```
