# Step 3 — Wire the mirror in `ICoderApp`, prove end-to-end, document

**Goal:** `ICoderApp.compose()` constructs `OutputLog` with
`mirror=self._core.event_log.write_chat`. A pilot integration test
drives the app through real input and asserts the on-disk `_chat.txt`
matches the visible conversation lines (including blank spacers).
Docs gain a short reference.

Refer to `pr_info/steps/summary.md`. Steps 1 and 2 must be merged
first.

## WHERE

- **Implementation:** `src/mcp_coder/icoder/ui/app.py`
- **Integration test:** `tests/icoder/test_app_pilot.py`
- **Docs:** `docs/icoder/icoder.md`

## WHAT

### Production change

In `ICoderApp.compose()`, change exactly one line:

```python
# before
yield OutputLog()
# after
yield OutputLog(mirror=self._core.event_log.write_chat)
```

No other code in `app.py` changes. The callback is a bound method;
when `EventLog.rotate()` runs on `/clear` or `prepare_for_resume`,
the bound method still references the same `EventLog` instance, so
subsequent mirror calls land in the freshly opened `_chat.txt`. No
need to re-pass the callback after rotation.

### Integration test

Append one test to `tests/icoder/test_app_pilot.py` (existing
`textual_integration` marker applies):

```python
async def test_chat_txt_mirrors_visible_conversation(tmp_path): ...
```

Construct the app with a `FakeLLMService` (already used elsewhere in
the file — follow the existing pattern), pointing the `EventLog` at
`tmp_path / "logs"`. Drive a tiny scripted run via Textual `Pilot`:

1. Submit user input `"hello"` (a non-command so it would normally
   stream — but with the fake service it returns deterministic
   text + a `done` event).
2. After the pilot settles, read
   `event_log.current_chat_path` from disk and assert:
   - The user line `"> hello"` is present.
   - The blank-line spacer falls AFTER the user line and before
     the assistant text — e.g.
     `chat_text.index("> hello") < chat_text.index("\n\n")` (or
     equivalently `re.search(r"> hello\n+\n", chat_text)`). This
     locks in turn ordering, not just spacer presence.
   - The fake assistant text `"fake response"` is present (this is
     `FakeLLMService`'s deterministic default reply, cross-checked
     in `test_llm_streaming` in the same module).

Keep the test compact; the goal is end-to-end proof, not coverage
duplication of step 1 / step 2 unit tests.

### Docs change

Append a short subsection to `docs/icoder/icoder.md` (e.g. near the
session-picker / log layout section, or under a new "Log files"
heading if none exists). Two or three sentences:

> Each session writes two files in `logs/`: a structured
> `icoder_<timestamp>.jsonl` (the authoritative replay log) and a
> sibling `icoder_<timestamp>_chat.txt` mirroring the visible
> conversation in plain text for copy/paste. The `.txt` is
> best-effort — if it cannot be opened or written, iCoder continues
> with only the `.jsonl` and logs a warning.

## HOW

- The only production-code change is the one-line edit in
  `compose()`. Verify by `git diff src/mcp_coder/icoder/ui/app.py`.
- The integration test reuses existing `FakeLLMService` /
  `tmp_path` patterns from `test_app_pilot.py`; do **not** invent a
  new fixture style.
- The test must run under `pytest -m textual_integration` (the
  marker is already set at module scope where used). Do not add new
  markers.

## ALGORITHM (pseudocode for the integration test)

```
async def test_chat_txt_mirrors_visible_conversation(tmp_path):
    logs_dir = tmp_path / "logs"
    event_log = EventLog(logs_dir=logs_dir)
    emit_session_start(event_log, provider="fake")
    core = AppCore(FakeLLMService(...), event_log, ...)
    app = ICoderApp(core)
    async with app.run_test() as pilot:
        await pilot.pause()
        await type_and_submit(pilot, "hello")
        await pilot.pause()  # let the worker / call_from_thread settle
    chat_text = event_log.current_chat_path.read_text(encoding="utf-8")
    assert "> hello" in chat_text
    # blank-line spacer survived AND falls after the user line
    assert chat_text.index("> hello") < chat_text.index("\n\n")
    assert "fake response" in chat_text  # FakeLLMService default reply
```

## DATA

- No new public APIs in this step. Only the constructor call to
  `OutputLog` is changed.
- The `.txt` on disk is the data structure under test — newline-
  terminated lines, no escaping, no Markdown.

## TDD — Tests to add first

1. **`test_chat_txt_mirrors_visible_conversation`** (described
   above) fails on `main` because `OutputLog()` is constructed
   without a mirror; the `.txt` exists but is empty. Adding the
   one-line wiring in `compose()` flips it to green.

The unit-level mirror behavior is already covered by step 2; the
file-pairing behavior is covered by step 1. This integration test is
the end-to-end proof and intentionally narrow.

## Implementation order (TDD loop)

1. Add the integration test in `tests/icoder/test_app_pilot.py`.
   Run pytest to confirm it fails (`> hello` not found in empty
   `.txt`).
2. Edit `ICoderApp.compose()` to pass
   `mirror=self._core.event_log.write_chat` to `OutputLog()`. Re-run
   pytest until the new test and all existing tests pass.
3. Append the docs subsection to `docs/icoder/icoder.md`.
4. Run all three quality gates per `CLAUDE.md`:
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__tools-py__run_mypy_check`
   - Note: this is the one step where the `textual_integration`
     marker matters — verify the new test runs by *not* excluding
     `textual_integration` from the marker filter. The recommended
     filter above already does not exclude it.
5. Stage + commit (one commit). Message suggestion:
   `iCoder: mirror conversation to plain-text chat log (#982)`.

## Verification beyond green tests

- `/clear`: type `/clear` in the running app; confirm the old
  `_chat.txt` is left on disk untouched and a fresh `_chat.txt`
  starts receiving the post-clear conversation (this is structural —
  step 1 guarantees the rotation; this is just a smoke check).
- `/load` resume: pick a prior session; confirm a new `_chat.txt`
  pair is created and the replayed banner / prior turns land in it.

## Out of scope for this step

- Re-deriving the `.txt` filename anywhere outside step 1.
- Adjusting `list_icoder_logs` — `.txt` must remain invisible to the
  picker (it already is, because the picker filters on `.jsonl`
  `session_start.provider`).
- Any clipboard integration.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`, and
> confirm steps 1 and 2 are already merged (`EventLog.write_chat`
> exists and `OutputLog` accepts a `mirror=` parameter). Implement
> step 3 only. Strictly TDD: add
> `test_chat_txt_mirrors_visible_conversation` in
> `tests/icoder/test_app_pilot.py` first (use the existing
> `FakeLLMService` pattern from that module). Confirm it fails. Then
> change `ICoderApp.compose()` in `src/mcp_coder/icoder/ui/app.py`
> to construct `OutputLog(mirror=self._core.event_log.write_chat)`.
> Add a short "Log files" note to `docs/icoder/icoder.md`. Use only
> MCP tools per `CLAUDE.md`. Run all three quality gates
> (`run_pylint_check`, `run_pytest_check` with `-n auto` and the
> integration-exclusion `-m` filter — note `textual_integration`
> must remain enabled — and `run_mypy_check`) until they all pass.
> Stage and commit exactly one commit when green.
