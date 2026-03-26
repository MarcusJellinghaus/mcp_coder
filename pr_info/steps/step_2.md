# Step 2: stream_subprocess() in subprocess_runner

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 2: add `stream_subprocess()` generator function to `src/mcp_coder/utils/subprocess_runner.py`. Follow TDD — write tests first in `tests/utils/test_subprocess_runner.py`, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(subprocess): add stream_subprocess generator`.

## WHERE

- **Modify**: `src/mcp_coder/utils/subprocess_runner.py`
- **Modify**: `tests/utils/test_subprocess_runner.py`

## WHAT

### New function in `subprocess_runner.py`:

```python
def stream_subprocess(
    command: list[str],
    options: CommandOptions | None = None,
) -> Iterator[str]:
    """Execute a command and yield stdout lines as they arrive.

    Unlike execute_subprocess() which buffers all output, this generator
    yields each line of stdout in real-time. After iteration completes,
    the final CommandResult is available via the generator's return value
    (accessible via StopIteration.value or a wrapper).

    Args:
        command: Command and arguments as a list
        options: Execution options (timeout, env, cwd, etc.)

    Yields:
        Individual lines from stdout (without trailing newline)

    Returns:
        CommandResult with final execution details (via generator return)

    Raises:
        TypeError: If command is None.
    """
```

### New wrapper class:

```python
class StreamResult:
    """Wrapper that iterates stream lines and captures the final CommandResult.

    Usage:
        stream = StreamResult(stream_subprocess(command, options))
        for line in stream:
            process(line)
        result = stream.result  # CommandResult after iteration
    """

    def __init__(self, gen: Iterator[str]) -> None: ...
    def __iter__(self) -> Iterator[str]: ...
    def __next__(self) -> str: ...
    @property
    def result(self) -> CommandResult: ...
```

## HOW

- Add `Iterator` to imports from `typing` (or `collections.abc`)
- Add `stream_subprocess` and `StreamResult` to `__all__`
- Reuse existing env setup logic: `is_python_command()`, `get_python_isolation_env()`, `get_utf8_env()`
- The function uses `subprocess.Popen` with `stdout=subprocess.PIPE` and reads line-by-line
- Timeout is handled by a background timer that kills the process
- stderr is captured fully (buffered) via `subprocess.PIPE`

## ALGORITHM

```
def stream_subprocess(command, options):
    env = prepare_env(command, options)  # reuse existing env logic
    proc = Popen(command, stdout=PIPE, stderr=PIPE, env=env, cwd=options.cwd, text=True)
    start_time = time.time()
    try:
        for line in proc.stdout:
            if time.time() - start_time > options.timeout_seconds:
                kill_process(proc)
                return CommandResult(timed_out=True, ...)
            yield line.rstrip('\n')
        proc.wait()
        stderr = proc.stderr.read() if proc.stderr else ""
        return CommandResult(return_code=proc.returncode, stdout="", stderr=stderr, timed_out=False, ...)
    except GeneratorExit:
        kill_process(proc)
```

## DATA

### Input
- Same `CommandOptions` as `execute_subprocess()`

### Output (yield)
- `str` — individual stdout lines, newline stripped

### Output (return via StopIteration.value / StreamResult.result)
- `CommandResult` — note: `stdout` is empty string (lines were already yielded)

## TEST CASES (write first)

1. `test_stream_subprocess_yields_lines` — run `echo` command, verify lines yielded
2. `test_stream_subprocess_returns_command_result` — verify `StreamResult.result` has correct return_code
3. `test_stream_subprocess_captures_stderr` — command writes to stderr, verify in result
4. `test_stream_subprocess_timeout` — long-running command, verify timed_out=True in result
5. `test_stream_subprocess_none_command_raises` — verify TypeError for None command
6. `test_stream_subprocess_env_setup` — verify Python commands get isolation env
7. `test_stream_result_wrapper_iteration` — verify StreamResult wraps generator correctly
