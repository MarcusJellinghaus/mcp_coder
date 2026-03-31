# Step 1: Subprocess Inactivity Watchdog Timeout

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Replace the one-shot `threading.Timer` in `stream_subprocess()` with a watchdog
daemon thread that implements **inactivity timeout** (reset on each yielded line).

## WHERE

- **Modify:** `src/mcp_coder/utils/subprocess_streaming.py`
- **Create:** `tests/utils/test_subprocess_streaming.py`

## WHAT

### `subprocess_streaming.py` — Replace timer with watchdog

Remove the `threading.Timer` block. Add a watchdog daemon thread that:

```python
# PSEUDOCODE (watchdog pattern)
last_activity = time.time()          # shared mutable; updated by main thread
stop_event = threading.Event()       # signal watchdog to exit

def _watchdog():
    while not stop_event.wait(timeout=1):          # check every 1s
        if time.time() - last_activity > timeout:
            timed_out = True
            proc.kill()
            return

# In the yield loop:
for line in proc.stdout:
    last_activity = time.time()      # reset on each line
    yield line.rstrip("\n")

# In finally:
stop_event.set()
watchdog_thread.join(timeout=5)
```

**Function signature unchanged:** `stream_subprocess(command, options) -> Generator[str, None, CommandResult]`

The `CommandOptions.timeout_seconds` field keeps its existing name and default (120).
The semantic change is: for `stream_subprocess` it now means inactivity timeout;
for `execute_subprocess` it remains total timeout (unchanged).

### `test_subprocess_streaming.py` — New test file

Tests:

1. **`test_stream_inactivity_timeout_kills_process`**: Launch a process that prints
   one line then sleeps forever. Set `timeout_seconds=2`. Assert iteration completes
   and `result.timed_out is True`.

2. **`test_stream_active_process_no_timeout`**: Launch a process that prints lines
   with small delays (0.5s each). Set `timeout_seconds=2`. Assert all lines received
   and `result.timed_out is False`.

3. **`test_stream_subprocess_basic`**: Existing basic test — process prints lines and
   exits. Assert lines match and `timed_out is False`.

## HOW

- The watchdog thread is a plain `threading.Thread(daemon=True)`.
- `last_activity` is a plain `float` — no lock needed since only one writer (main
  thread) and one reader (watchdog), and float assignment is atomic in CPython.
- `stop_event` is a `threading.Event` used to cleanly exit the watchdog.
- The `finally` block sets `stop_event` and joins the watchdog (same as current timer cancel).

## DATA

No changes to `CommandResult` or `CommandOptions` dataclasses. The `timed_out` field
and `execution_error` message work identically.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement step 1: Replace the threading.Timer in stream_subprocess()
(src/mcp_coder/utils/subprocess_streaming.py) with a watchdog daemon thread that
implements inactivity timeout. Write tests first in
tests/utils/test_subprocess_streaming.py, then implement. Run all three MCP code
quality checks after changes. Commit message: "icoder: inactivity watchdog timeout
for stream_subprocess"
```
