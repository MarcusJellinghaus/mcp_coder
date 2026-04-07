# Step 4: Add subprocess integration test for real crash capture

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #712).

## LLM Prompt

```
Implement step 4 of issue #712 (see pr_info/steps/summary.md for context).

Add a subprocess integration test that spawns a child process, triggers a real
faulthandler crash via faulthandler._sigsegv(), and asserts the crash log file
contains a Python traceback. Run all three quality checks after implementation.
```

## WHERE

- **Modify**: `tests/utils/test_crash_logging.py` (add one test)

## WHAT

One new test: `test_crash_log_captures_real_segfault`

## HOW

- Use `subprocess.run` to spawn a child Python process
- Child process script (inline):
  1. Calls `enable_crash_logging(tmp_dir, "test")`
  2. Calls `faulthandler._sigsegv()` to trigger a real crash
- Parent process:
  1. Asserts child exited with non-zero code
  2. Finds the crash log file in `{tmp_dir}/logs/faulthandler/`
  3. Reads it and asserts it contains traceback markers (e.g., `"Fatal Python error"` or `"Current thread"`)

## ALGORITHM

```
script = textwrap.dedent("""
    import sys
    from pathlib import Path
    import faulthandler
    from mcp_coder.utils.crash_logging import enable_crash_logging
    enable_crash_logging(Path(sys.argv[1]), "test")
    faulthandler._sigsegv()  # triggers real crash
""")
result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], ...)
assert result.returncode != 0
crash_files = list((tmp_path / "logs" / "faulthandler").glob("crash_test_*.log"))
assert len(crash_files) == 1
content = crash_files[0].read_text()
assert "Fatal Python error" in content or "Current thread" in content
```

## DATA

- No new production code
- Test uses `tmp_path` fixture
- Comment in test explains why `faulthandler._sigsegv()` (private API) is acceptable: it's CPython's standard test hook, used by CPython's own test suite

## Notes

- No new pytest marker needed — this is a standard test that happens to use subprocess
- The child process will crash (expected), so `check=False` on `subprocess.run`
- If the `_sigsegv()` subprocess test proves flaky on Windows during implementation, fall back to asserting the crash log file exists and is non-empty (rather than asserting traceback content). Strong assertion is preferred since faulthandler is designed for cross-platform crash capture.
