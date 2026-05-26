# Step 1 — Pair `EventLog` with a plain-text `.txt` sidecar

**Goal:** `EventLog` owns both `icoder_<ts>.jsonl` and
`icoder_<ts>_chat.txt`. The two files share a stem (including any
collision suffix), rotate together, close together, and the `.txt`
opens/writes best-effort so a failure cannot break iCoder.

Refer to `pr_info/steps/summary.md` for the full architectural
overview.

## WHERE

- **Implementation:** `src/mcp_coder/icoder/core/event_log.py`
- **Tests:** `tests/icoder/test_event_log.py`

## WHAT

Add the following inside `src/mcp_coder/icoder/core/event_log.py`:

```python
def _chat_path_for(jsonl_path: Path) -> Path: ...
```

Inside `class EventLog`:

```python
# new field
self._chat_file: IO[str] | None  # opened best-effort in __init__

def write_chat(self, line: str) -> None: ...

@property
def current_chat_path(self) -> Path: ...  # for tests + UI wiring
```

Update existing methods:

- `EventLog.__init__` — after computing `self._path`, derive
  `self._chat_path = _chat_path_for(self._path)` and try to open it
  for append. On `OSError`, log a warning via `logger.warning(...)`
  and set `self._chat_file = None`. JSONL must still open.

- `EventLog.rotate` — after switching `self._path` to the new JSONL
  path, close the old chat file (if any), derive a new chat path
  from the new JSONL path, and try to open it (same best-effort
  policy). Return the new JSONL path unchanged.

- `EventLog.close` — also flush + close `self._chat_file` when
  present.

## HOW

- **Module logger:** add `logger = logging.getLogger(__name__)` at
  module top (and `import logging`). All warnings on `.txt` failures
  go through it.
- **Path derivation:**
  `jsonl_path.with_name(jsonl_path.stem + "_chat.txt")`. Crucially
  this is derived from the *chosen* `.jsonl` path so the `-2` /
  `-3` collision suffixes from `_allocate_log_path` carry over.
- **Best-effort policy is centralised in a small private helper.**
  This helper is the single chokepoint for opening the chat file
  (called from `__init__` and `rotate`), which makes it the patch
  target for test #6 below:

  ```python
  def _try_open_chat(path: Path) -> IO[str] | None:
      try:
          return open(path, "a", encoding="utf-8")  # noqa: SIM115
      except OSError as exc:
          logger.warning("iCoder chat mirror disabled (%s): %s", path, exc)
          return None
  ```

- **`write_chat` is a no-op when `_chat_file is None`** and downgrades
  itself on write failure (closes the file, sets the attribute to
  `None`, logs once). It never raises.

## ALGORITHM (pseudocode)

```
__init__(logs_dir):
    create logs_dir
    self._path = _allocate_log_path(logs_dir)
    open jsonl for append → self._file
    self._chat_path = _chat_path_for(self._path)
    self._chat_file = _try_open_chat(self._chat_path)  # may be None

write_chat(line):
    if self._chat_file is None: return
    try: write line + "\n"; flush
    except OSError: log warning; close; self._chat_file = None

rotate():
    flush+close jsonl; flush+close chat (if any)
    new_jsonl = _allocate_log_path(self._logs_dir)
    open new jsonl → self._file
    self._path = new_jsonl
    self._chat_path = _chat_path_for(new_jsonl)
    self._chat_file = _try_open_chat(self._chat_path)
    reset clock + entries
    return new_jsonl

close():
    close jsonl (if open); close chat (if open)
```

## DATA

- `_chat_path_for(jsonl: Path) -> Path` returns a path with stem
  ending in `_chat` and suffix `.txt`. Examples:
  `icoder_2026-05-26T10-00-00-123456.jsonl` →
  `icoder_2026-05-26T10-00-00-123456_chat.txt`;
  `icoder_…-2.jsonl` → `icoder_…-2_chat.txt`.
- `EventLog.write_chat(line: str) -> None` — never raises.
- `EventLog.current_chat_path -> Path` — always present (even when
  the file failed to open); callers must not assume the file exists.

## TDD — Tests to add first

Append to `tests/icoder/test_event_log.py` (no new module needed).
Markers: existing module-level markers apply; no new markers.

1. **`test_chat_sidecar_created_alongside_jsonl(tmp_path)`**
   Construct `EventLog(logs_dir=tmp_path)`; assert
   `log.current_chat_path.exists()` and the stem equals
   `log.current_path.stem + "_chat"`.

2. **`test_write_chat_appends_and_flushes(tmp_path)`**
   Call `log.write_chat("hello")` and `log.write_chat("")`; read the
   `.txt`; expect `"hello\n\n"` (the empty-string call must produce a
   bare newline — it's the spacer between turns).

3. **`test_rotate_pairs_files_with_matching_stems(tmp_path)`**
   Capture old paths; call `log.rotate()`; assert both
   `current_path` and `current_chat_path` changed and share a stem;
   assert the old files are still on disk untouched.

4. **`test_rotate_preserves_collision_suffix(tmp_path, monkeypatch)`**
   Monkeypatch `_make_log_filename` to return a constant; construct
   two `EventLog`s back-to-back (or call `rotate` twice with a fixed
   timestamp); assert the second JSONL ends with `-2.jsonl` and the
   second chat file ends with `-2_chat.txt`.

5. **`test_close_closes_both_files(tmp_path)`**
   Construct, call `close()`, assert `log._file.closed` and (when
   `log._chat_file` is not `None`) `log._chat_file.closed`.

6. **`test_chat_open_failure_is_best_effort(tmp_path, monkeypatch, caplog)`**
   Monkeypatch the private helper
   `mcp_coder.icoder.core.event_log._try_open_chat` so it simulates
   a failed open — e.g. replace it with a function that logs the
   same warning `_try_open_chat` would emit on `OSError` and
   returns `None` (the simplest form is
   `monkeypatch.setattr("mcp_coder.icoder.core.event_log._try_open_chat", lambda path: None)`,
   combined with an explicit `caplog`-level assertion that step 1's
   implementation logs the warning at the call site, or a patch
   that raises `OSError` internally and lets the production helper
   handle it). Because the helper is the single chokepoint for
   opening the chat file (see HOW section), this patch covers both
   `__init__` and the post-rotate open path without touching the
   builtin `open`. Construct `EventLog(logs_dir=tmp_path)`. Assert:
   JSONL is open and usable; `log._chat_file is None`;
   `log.write_chat("x")` does not raise; a warning was logged.

## Implementation order (TDD loop)

1. Add the six tests above (they fail because methods/fields don't
   exist).
2. Add `_chat_path_for`, the `_try_open_chat` helper, the `_chat_file`
   field, `write_chat`, the rotate/close wiring, and
   `current_chat_path`. Run pytest until all new tests pass and the
   existing event-log tests stay green.
3. Run all three quality gates per `CLAUDE.md`:
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__tools-py__run_mypy_check`
4. Stage + commit (one commit). Message suggestion:
   `iCoder: pair EventLog with plain-text chat sidecar (#982)`.

## Out of scope for this step

- No `OutputLog` change.
- No wiring in `ICoderApp`.
- No documentation change.

These belong to steps 2 and 3.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
> Implement step 1 only. Strictly TDD: add the six failing tests in
> `tests/icoder/test_event_log.py` first, then add the matching
> implementation in `src/mcp_coder/icoder/core/event_log.py`
> (`_chat_path_for`, `_try_open_chat`, `_chat_file`, `write_chat`,
> paired rotation in `rotate()`, paired close in `close()`,
> `current_chat_path`). Do not touch `OutputLog`, `ICoderApp`, or the
> docs — those are later steps. Use only MCP tools per `CLAUDE.md`.
> Run all three quality gates (`run_pylint_check`,
> `run_pytest_check` with `-n auto` and the integration-exclusion
> `-m` filter, `run_mypy_check`) until they all pass. Stage and
> commit exactly one commit when green.
