# Summary — iCoder plain-text chat mirror (`_chat.txt`)

## Goal

Add a sibling plain-text log file `logs/icoder_<timestamp>_chat.txt` next to
the existing `logs/icoder_<timestamp>.jsonl`. The `.txt` mirrors what is
visible in the iCoder TUI's `OutputLog` conversation area (including the
blank-line spacers between turns), so users can copy/paste conversations
into bug reports, PRs, Slack, etc. The Textual TUI does not support
reliable text selection; the file on disk is the workaround.

Tracking issue: **#982**.

## Guiding principle

> The `.txt` mirrors the TUI's visible conversation output.

Everything that lands in `OutputLog` — user lines, assistant text, tool
start blocks, tool result blocks (`│ … └ done`), runtime banner,
resumed/cancelled/error markers, **and the blank-line spacers between
turns** — is mirrored. Everything outside the conversation area (status
bar, branch info bar, busy indicator, in-flight streaming tail) is not.

## Architectural / design changes

The minimum coupling that preserves all issue requirements:

1. **`EventLog` owns both files as a pair.**
   `src/mcp_coder/icoder/core/event_log.py` already owns the JSONL file
   and its rotation. The `.txt` sidecar is added there — same open
   point, same `rotate()` point, same `close()` point. The `.txt` path
   is derived from the chosen `.jsonl` path
   (`jsonl.with_name(jsonl.stem + "_chat.txt")`) so collision suffixes
   like `-2` are inherited automatically and the pair can never
   desynchronize. No new class, no extra rotation wiring in
   `app_core.py`.

2. **`OutputLog` gains a one-arg `mirror` callback.**
   `src/mcp_coder/icoder/ui/widgets/output_log.py` takes
   `mirror: Callable[[str], None] | None = None` and calls it from the
   same call sites that already populate `_recorded`, plus the `write("")`
   path used for blank-line spacers. The widget remains ignorant of
   `EventLog` — clean layering preserved.

3. **`ICoderApp.compose()` wires the callback.**
   `src/mcp_coder/icoder/ui/app.py` passes
   `mirror=self._core.event_log.write_chat` when constructing
   `OutputLog`. One line of glue. Replay populates the `.txt` for free
   because `replay_log` re-renders through `append_text` /
   `_handle_stream_event`, both of which flow through the mirrored
   `OutputLog`.

4. **Failure handling is best-effort.**
   If the `.txt` cannot be opened or written (permission denied, disk
   full, read-only FS, AV lock), `EventLog` logs a warning and
   continues with only the JSONL. iCoder never hard-fails on `.txt`
   errors. JSONL remains the authoritative record.

5. **Out of scope (unchanged):** status bar, branch info bar, busy
   indicator, streaming tail, picker filter (`list_icoder_logs` still
   filters on `.jsonl` `session_start.provider`), clipboard
   integration. Threading model unchanged — all `OutputLog` writes
   already run on the Textual UI thread.

## Files created / modified

### Modified — source code

- `src/mcp_coder/icoder/core/event_log.py`
  Add `_chat_path_for` helper, `_chat_file: IO[str] | None`, attempt
  open in `__init__`, `write_chat(line: str)` method, rotate the
  sidecar inside `rotate()`, close it inside `close()`. All `.txt`
  operations are best-effort and swallow `OSError` with a logged
  warning.

- `src/mcp_coder/icoder/ui/widgets/output_log.py`
  Add `mirror: Callable[[str], None] | None = None` constructor
  parameter. Invoke `self._mirror(...)` from the existing three
  recording points: string `write()` (blank spacers), non-`Text`
  renderable `write()` (e.g. Markdown), and `append_text()`.

- `src/mcp_coder/icoder/ui/app.py`
  Pass `mirror=self._core.event_log.write_chat` to `OutputLog()` in
  `compose()`.

### Modified — tests

- `tests/icoder/test_event_log.py`
  Add tests for paired-file creation, `write_chat`, paired rotation
  (including collision suffix), paired close, and `.txt`-open-failure
  graceful degradation.

- `tests/icoder/ui/test_output_log.py`
  Add tests asserting the mirror callback is invoked from `write("")`,
  `write(Markdown(...))`, and `append_text("…")`.

- `tests/icoder/test_app_pilot.py`
  Add one pilot integration test: drive a couple of inputs through the
  app and assert the on-disk `_chat.txt` reflects the visible
  conversation (user lines + blank-line spacers).

### Modified — docs

- `docs/icoder/icoder.md`
  Add a short note describing the sibling `_chat.txt` file and its
  best-effort nature.

### Created

- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`,
  `pr_info/steps/step_3.md`

## Step overview

| Step | Layer | What | One commit covers |
|------|-------|------|-------------------|
| 1 | core | Pair the `.txt` sidecar with `EventLog` | tests + impl + checks for `EventLog` |
| 2 | UI widget | Mirror callback in `OutputLog` | tests + impl + checks for `OutputLog` |
| 3 | UI app + docs | Wire callback in `compose()`, pilot integration test, docs note | tests + impl + checks for end-to-end |

Each step is independent: step 1 is plain Python with no Textual
dependency; step 2 is the widget; step 3 is the wiring + integration
proof + docs. Each ends with **all three quality gates passing**:
`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
(with `-n auto` plus the integration-exclusion `-m` pattern), and
`mcp__tools-py__run_mypy_check`.
