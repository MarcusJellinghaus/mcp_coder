# Step 2 — Capture helper and retry loop in `_env.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (sections §2, §3 and "Hard constraints") and this file.
> Implement step 2 only: add the stderr capture-and-match helper and the `retry_on`
> retry loop to `src/mcp_coder/install/_env.run()`. Do **not** touch any call site yet
> (step 3). Write `tests/install/test_install_retry.py` first, then the code. Update the
> `_env.py` module docstring and the `.importlinter` comment. Run ruff check, pylint,
> mypy, lint-imports and the fast unit tests (CLAUDE.md), format, and make one commit.
> Precondition: step 1 is done (`run()` echoes via `logger.log(OUTPUT, ...)`). If it is
> not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE
- `src/mcp_coder/install/_env.py` (code, constants, module docstring)
- `.importlinter` — comment above `[importlinter:contract:subprocess_isolation]` only
- `tests/install/test_install_retry.py` (new)

## WHAT

```python
Signature = tuple[str, tuple[str, ...]]   # (id, regexes); all regexes must match

UV_TRANSIENT_SIGNATURES: tuple[Signature, ...] = (
    ("ENV-PYPI-NETWORK", (r"Failed to fetch: `?https://pypi\.org",)),
    ("ENV-UV-ACCESS-DENIED-CACHE",
        (r"Failed to persist temporary file", r"Access is denied")),
)
_STDERR_TAIL_BYTES = 64 * 1024
_READ_CHUNK_BYTES = 64 * 1024
_READER_JOIN_TIMEOUT_SECONDS = 5.0
_UV_RETRY_DELAY_SECONDS = 10

def _can_capture_stderr() -> bool: ...
def _match_signature(text: str, signatures: Sequence[Signature]) -> str | None: ...
def _drain_stderr(stream: IO[bytes], tail: bytearray) -> None: ...
def _run_capturing(
    command: list[str], signatures: Sequence[Signature], cwd: Path | None
) -> tuple[int, str | None]: ...

def run(cmd: list[str], *, check: bool = True, dry: bool = False,
        cwd: Path | None = None, retry_on: tuple[Signature, ...] = ()) -> int: ...
```

New imports in `_env.py`: `logging` (already from step 1), `re`, `threading`,
`collections.abc.Sequence`, `typing.IO`, `OUTPUT` (already from step 1).

## HOW
- `run()` docstring: document `retry_on` ("signatures that allow one retry after
  `_UV_RETRY_DELAY_SECONDS`; only used when stderr is not a terminal").
- Module docstring: keep the reason for raw `subprocess` (shared `execute_command`
  captures and times out; `stream_subprocess` is line-based and mangles `\r`), and add:
  when stderr is not a terminal and `retry_on` is given, only stderr is piped, relayed
  byte for byte to `sys.stderr.buffer` and its tail matched against the signatures.
- `.importlinter` comment: change "need inherited TTY/stdio and no timeout" wording for
  `install.**` to "uv/pip with live progress output (inherited stdio, or a raw stderr
  pipe relayed byte for byte when stderr is not a terminal)". `ignore_imports` unchanged.
- Retry log text (exact; must never contain `WARNING` or `ERROR:`):
  - `"--- uv failed with a transient error (%s); retrying once in %d s"` (id, delay)
  - `"--- uv retry succeeded"`
- `proc.stderr` None-check: follow the existing pattern
  `assert proc.stderr is not None  # noqa: S101 -- stderr=PIPE always sets it`.

## ALGORITHM

```
run: echo "> cmd"; if dry: return 0
  if retry_on and _can_capture_stderr():
      rc, hit = _run_capturing(cmd, retry_on, cwd)
      if rc != 0 and hit: log retry line; time.sleep(DELAY); rc, _ = _run_capturing(...)
                          if rc == 0: log "--- uv retry succeeded"
  else: rc = subprocess.run(cmd, cwd=cwd, check=False).returncode
  if check and rc != 0: sys.exit(rc); return rc
```

```
_run_capturing: proc = Popen(command, cwd=cwd, stderr=PIPE)   # stdout inherited, no `with`
  tail = bytearray(); start daemon Thread(_drain_stderr, args=(proc.stderr, tail))
  try: rc = proc.wait()  except BaseException: proc.kill(); raise
  reader.join(_READER_JOIN_TIMEOUT_SECONDS)        # never close proc.stderr afterwards
  return rc, _match_signature(bytes(tail).decode("utf-8", errors="replace"), signatures)
```

```
_drain_stderr: try fd = stream.fileno() except (OSError, ValueError): return
  loop: try chunk = os.read(fd, _READ_CHUNK_BYTES) except OSError: return
        if not chunk: return
        tail.extend(chunk); del tail[:-_STDERR_TAIL_BYTES]
        try: sys.stderr.flush(); sys.stderr.buffer.write(chunk); sys.stderr.buffer.flush()
        except (OSError, ValueError, AttributeError): pass   # keep draining, never stop
```

- `_can_capture_stderr`: `stream = sys.stderr`; return `stream is not None and
  hasattr(stream, "buffer") and not stream.isatty()`.
- `_match_signature`: first `sig_id` whose regexes all `re.search(rx, text)`, else None.
- The reader gets the **stream object**, not its fd (keeps the stream alive while the
  thread runs). Each attempt creates its own `tail`.

## DATA
- `_run_capturing` → `(exit_code, matched_id_or_None)`; match is computed regardless of
  exit code; `run()` only retries when `rc != 0`.
- `run()` return value and `sys.exit` behaviour unchanged.

## Tests — `tests/install/test_install_retry.py` (write first)

Real log text (user path anonymised):

```python
PYPI_ERROR = (
    "error: Failed to fetch: `https://pypi.org/simple/flask-cors/`\n"
    "  Caused by: connection error\n"
    "  Caused by: stream closed because of a broken pipe\n"
)
CACHE_ERROR = (
    "error: Failed to write to the client cache\n"
    "  Caused by: Failed to persist temporary file to "
    "C:\\Users\\builder\\AppData\\Local\\uv\\cache\\simple-v14\\pypi\\starlette.rkyv: "
    "Access is denied. (os error 5)\n"
)
```

Helpers:
- `_scripted_child(tmp_path, attempts: list[tuple[int, str]]) -> list[str]`: writes a
  small Python script plus a counter file to `tmp_path`; each invocation reads/increments
  the counter, writes `attempts[i][1]` to `sys.stderr.buffer` (UTF-8) and exits with
  `attempts[i][0]`. Returns `[sys.executable, script, counter_file]`. Real child
  processes; `tests.install.**` is exempt from `subprocess_isolation`.
- Autouse fixture: `monkeypatch.setattr(_env.time, "sleep", recorder)` (shared with
  `rmtree_with_retry`; monkeypatch restores it) and
  `caplog.set_level(OUTPUT, logger="mcp_coder.install")`.
- Capture-path tests force `monkeypatch.setattr(_env, "_can_capture_stderr", lambda: True)`
  and replace `sys.stderr` with `io.TextIOWrapper(io.BytesIO(), encoding="utf-8")` so
  relayed bytes can be read back from `.buffer.getvalue()` (`monkeypatch.setattr(sys, "stderr", …)`).

Test cases:
1. `test_transient_error_retries_once_then_succeeds` — parametrized over
   `("ENV-PYPI-NETWORK", PYPI_ERROR)` and `("ENV-UV-ACCESS-DENIED-CACHE", CACHE_ERROR)`;
   attempts `[(2, text), (0, "")]`; `run(cmd, retry_on=UV_TRANSIENT_SIGNATURES)` returns
   0; sleep called once with 10; exactly one message
   `f"--- uv failed with a transient error ({id}); retrying once in 10 s"` and exactly one
   `"--- uv retry succeeded"`; exactly one `> ` echo line; no message contains `WARNING`
   or `ERROR:`.
2. `test_two_transient_failures_exit_with_uv_code` — attempts `[(2, PYPI_ERROR)] * 2`;
   `SystemExit` with code 2; one retry line, no success line.
3. `test_other_error_is_not_retried` — `[(1, "error: No solution found when resolving dependencies\n")]`;
   `SystemExit` 1; sleep not called; counter shows one attempt; no retry line.
4. `test_partial_cache_signature_is_not_retried` — only `"Access is denied. (os error 5)"`
   (no "Failed to persist temporary file") → no retry.
5. `test_retry_line_does_not_match_signatures` — `_match_signature(<the retry line for each id>,
   UV_TRANSIENT_SIGNATURES) is None`.
6. `test_empty_retry_on_keeps_subprocess_run` — `_can_capture_stderr` forced True,
   `subprocess.run` patched with a recorder returning `returncode=0`;
   `run(cmd, cwd=tmp_path)` → recorder called once with `(cmd, cwd=tmp_path, check=False)`.
7. `test_no_capture_keeps_subprocess_run_and_no_retry` — `_can_capture_stderr` forced
   False, recorder returns `returncode=1`; `run(cmd, retry_on=UV_TRANSIENT_SIGNATURES)`
   → called exactly once as in 6, `SystemExit` 1, sleep not called.
8. `test_can_capture_stderr` — parametrized `sys.stderr` values: `None` → False;
   `io.StringIO()` (no `.buffer`) → False; a `TextIOWrapper` subclass whose `isatty()`
   returns True → False; `io.TextIOWrapper(io.BytesIO())` → True.
9. `test_relay_is_byte_exact` — child writes `b"50%\r100%\r\n"` via `sys.stderr.buffer`
   and exits 0; relayed buffer contains exactly those bytes (`\r` kept).
10. `test_tail_is_bounded` — child writes `PYPI_ERROR` followed by 200 KiB of `x` and
    exits 2 → `_run_capturing` returns `(2, None)`; reversed order → `(2, "ENV-PYPI-NETWORK")`.
11. `test_grandchild_holding_stderr_does_not_block` — patch
    `_env._READER_JOIN_TIMEOUT_SECONDS = 0.2`; child spawns
    `subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])` (inherits
    stderr) and exits 0; `time.monotonic()` around `run(cmd, retry_on=…)` < 3 s.
    Measure with `time.monotonic`, not the patched `_env.time.sleep`.
12. `test_relay_write_error_keeps_draining` — `sys.stderr` replaced by an object with
    `.buffer.write` raising `OSError` (no-op `flush()`, `isatty()` False); child writes 1 MiB to
    stderr and exits 0. Run `_run_capturing` in a helper thread, `join(60)`, assert the
    thread finished and returned `(0, None)` (a stopped reader would deadlock the child
    on a full pipe).
13. `test_wait_interrupt_kills_child` — patch `_env.subprocess.Popen` with a fake whose
    `stderr` is `open(read_fd, "rb")` from `os.pipe()` (write end closed → immediate EOF),
    `wait()` raises `KeyboardInterrupt`, `kill()` records; `_run_capturing` re-raises
    `KeyboardInterrupt` and `kill` was called.
