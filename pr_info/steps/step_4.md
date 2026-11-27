# Step 4 — Command toolkit steps log what they ran (DEBUG)

Read `pr_info/steps/summary.md` first.

## WHERE

- `src/mcp_coder/toolkits/command/toolkit.py`: `_run_step`
- `tests/toolkits/command/test_toolkit_run.py`: a new class `TestStepLogging`,
  plus `caplog` assertions added to the existing `TestFailures` tests

## WHAT

`_run_step(step: Step, project_dir: Path) -> ActionResult` keeps its signature
and return values. Only log calls and timing are added.

## HOW

Add `import time` to `toolkit.py`. Then:

- **Executable not found:** `logger.debug("%s", message)` before the return.
  `message` is already `"<label>: '<argv0>' not found"`.
- **The command run:** wrap `execute_command` with timing.

  ```python
  cmd = [exe, *step.argv[1:]]
  start = time.perf_counter()
  res = execute_command(cmd, cwd=str(project_dir), timeout_seconds=step.timeout)
  elapsed = time.perf_counter() - start
  ```

- **Timed out:** `logger.debug("%s", message)` before the return. `message` is
  `"<label>: timed out after N s"`.
- **Execution error:** `logger.debug("%s", message)` before the return.
  `message` is `"<label>: <error>"`.
- **Otherwise**, directly after the two early-return checks:

  ```python
  logger.debug("%s: ran %s, exit %s (%.1f s)", label, cmd, res.return_code, elapsed)
  ```

Every new line is DEBUG. They also appear for `run_binding`, the formatters and
`rebase_checks.py`, which is intended.

## ALGORITHM

```
exe = resolve(argv0); if None -> debug(message); return error
cmd = [exe, *argv[1:]]; start = perf_counter()
res = execute_command(cmd, ...); elapsed = perf_counter() - start
if timed_out -> debug(message); return error
if execution_error -> debug(message); return error
debug("<label>: ran <cmd>, exit <code> (<elapsed> s)"); continue as today
```

## DATA

An example DEBUG message:
`fakenpm lint: ran ['C:\\…\\fakenpm.cmd', 'lint'], exit 1 (0.3 s)`.

## Tests (write first)

In `tests/toolkits/command/test_toolkit_run.py`:

1. New `class TestStepLogging` with `test_step_logs_label_command_and_exit_code(fake_npm, project_dir, caplog)`:
   - `_exit_script(fake_npm, "lint", 1)` with config
     `{"check": {"q": [{"argv": ["fakenpm", "lint"]}]}}`.
   - Run under `caplog.at_level(logging.DEBUG, logger="mcp_coder.toolkits.command.toolkit")`.
   - Exactly one DEBUG record from that logger contains `fakenpm lint: ran`,
     contains `repr(resolve_executable("fakenpm", project_dir))`, contains
     `exit 1`, and matches `\(\d+\.\d s\)`. Use `repr` because a list logs its
     elements as reprs, which double the backslashes in Windows paths.
2. Extend the existing `TestFailures` tests `test_timeout`,
   `test_execution_error` and `test_argv0_not_found` with a `caplog` parameter
   and `caplog.at_level(logging.DEBUG, logger=...)` around the run. Assert a
   DEBUG record whose message equals `result.fix_text`, which is the label plus
   the status text. Assert that no record contains `": ran "`.

Keep `test_toolkit_run.py` under 750 lines (it is about 422 now).

## LLM prompt

> Implement Step 4 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_4.md`.
>
> 1. Write `TestStepLogging` and the `caplog` assertions in the `TestFailures`
>    tests of `tests/toolkits/command/test_toolkit_run.py`, and see them fail.
> 2. In `src/mcp_coder/toolkits/command/toolkit.py`, add the DEBUG lines and
>    timing to `_run_step` exactly as described; leave the return values
>    unchanged.
> 3. Run `run_format_code`, then pylint, mypy and pytest (fast unit set with
>    `-n auto`), and fix any findings.
> 4. Commit as one commit: `feat(toolkits): log each command step at DEBUG`.
