# Summary — #1369 install: retry a failed uv command once on transient errors

## Goal

`mcp-coder install` (and `mcp-coder setup`, whose `python` built-in calls `install()`
in-process) runs each uv command once. A transient uv failure — the PyPI network
error or the uv-cache "Access is denied" — fails the Jenkins step. This change retries
every `uv pip install` / `uv sync` call **once**, after a fixed **10 s** sleep, when
uv's stderr matches a known transient signature. Every other error fails immediately,
with uv's exit code, as today.

The full spec is issue #1369; this plan implements it without additions.

## Architectural / design changes

### 1. Install output goes through logging (stdout → stderr)
- Every `print()` in `src/mcp_coder/install/` becomes `logger.log(OUTPUT, ...)`
  (`OUTPUT` from `mcp_coder.utils.log_utils`; one `logger = logging.getLogger(__name__)`
  per module).
- The post-install failure summary header becomes `logger.error(...)`, without its own
  `ERROR: ` prefix (the `CleanFormatter` renders `ERROR: ` at the default level).
- Leading `\n` dropped from all messages: one log record = one line.
- Effect: install's lines now go to stderr, in order with uv's own stderr output
  (before, stdout was block-buffered in Jenkins and the `> uv …` echo landed late).
  `OUTPUT` is the default CLI level, so nothing becomes invisible at default verbosity.

### 2. `run()` gains an opt-in retry (`retry_on`)
`src/mcp_coder/install/_env.py`:

```
run(cmd, *, check=True, dry=False, cwd=None, retry_on=())   # retry_on: tuple[Signature, ...]
```

- `retry_on` empty (default) **or** stderr not capturable → today's
  `subprocess.run(cmd, cwd=cwd, check=False)` with inherited stdio, unchanged.
- Otherwise → `_run_capturing()`; on a non-zero exit with a matched signature:
  log `--- uv failed with a transient error (<ID>); retrying once in 10 s`, sleep 10 s,
  run once more; log `--- uv retry succeeded` if the retry exits 0. The command is
  not echoed again.
- Only the uv install/sync call sites pass `retry_on=UV_TRANSIENT_SIGNATURES`; every
  other `run()` call keeps today's code path by construction.

### 3. Generic capture-and-match helper (nothing uv-specific)
- `Signature = tuple[str, tuple[str, ...]]` — `(id, regexes)`; a signature matches when
  **all** its regexes `re.search` the decoded stderr tail. Plain tuples, no class.
- `_can_capture_stderr() -> bool` — False when `sys.stderr` is `None`, has no
  `.buffer`, or `isatty()`. The single switch that tests patch to pick a path.
- `_run_capturing(command, signatures, cwd) -> tuple[int, str | None]`:
  `Popen` with **only stderr piped** (stdout inherited); a `daemon=True` reader thread
  (`_drain_stderr`) does `os.read()` on the pipe, relays raw chunks to
  `sys.stderr.buffer` (flushing `sys.stderr` first) and keeps a bounded tail
  (new `bytearray` per attempt, ~64 KiB); `wait()` for uv (kill + re-raise if `wait()`
  raises); `join()` the reader with a 5 s timeout; never close the pipe and never use
  `with Popen`, so a grandchild still holding the pipe cannot hang the install.
- Module constants: `UV_TRANSIENT_SIGNATURES`, `_STDERR_TAIL_BYTES`,
  `_READER_JOIN_TIMEOUT_SECONDS`, `_READ_CHUNK_BYTES`, `_UV_RETRY_DELAY_SECONDS`.

### 4. Classifier suppression is data
- `tools/jenkins_issue_patterns.toml` gets two signatures (`MC-INSTALL-UV-RETRY`,
  `MC-INSTALL-UV-RETRY-OK`) and a `[classifier] no_status_suppressed_by` list.
- `tools/jenkins_classify_logs.py:classify` skips the PIPE-NO-STATUS id when an id from
  that list matched. A recovered build still contains uv's first error (which matches
  `pre_workflow` ENV ids), so without this it would be misreported.

### Unchanged on purpose
- `command_templates.py` (setup keeps its default `OUTPUT` level; no `--log-level`).
- `uv venv`, stdlib venv / pip fallbacks, `ensure_system_uv`'s `pip install uv`, the
  version report, post-install checks, dry run (`--check`).
- `install.**` keeps its `subprocess` exemption in `.importlinter`.
- The `sys.exit(...)` messages of `rmtree_with_retry` / `ensure_system_uv`.

### Hard constraints (every step)
- Retry lines must never contain `WARNING` or `ERROR:` (Jenkins findText → UNSTABLE).
- Signature regexes must not match the retry line; don't broaden them.
- Never retry on an arbitrary non-zero exit; only on a matched signature.

## Files

### Modified
| File | Step |
|---|---|
| `src/mcp_coder/install/__init__.py` | 1, 3 |
| `src/mcp_coder/install/_env.py` | 1, 2 |
| `src/mcp_coder/install/_phases.py` | 1, 3 |
| `tests/install/test_install_phases.py` | 1, 3 |
| `tests/install/test_install_post_checks.py` | 1 |
| `.importlinter` (comment only) | 2 |
| `docs/configuration/setup.md` | 3 |
| `docs/cli-reference.md` | 3 |
| `tools/jenkins_issue_patterns.toml` | 4 |
| `tools/jenkins_classify_logs.py` | 4 |
| `tools/jenkins_issue_analysis.md` | 4 |
| `tests/tools/test_jenkins_classify_logs.py` | 4 |

### Created
| File | Step |
|---|---|
| `tests/install/test_install_retry.py` | 2 |

No new packages or folders.

## Steps
1. `step_1.md` — Install output through logging (no behaviour change besides the stream).
2. `step_2.md` — Capture helper and retry loop in `_env.py` (+ docstring, `.importlinter` comment).
3. `step_3.md` — Pass `retry_on` at the uv install/sync call sites (+ user docs).
4. `step_4.md` — Classifier: retry signatures and PIPE-NO-STATUS suppression (+ analysis doc).

Each step is one commit: tests first, then implementation, then all checks green.
