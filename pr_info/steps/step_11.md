# Step 11 — CLI resume rewrite + startup picker + self-contained-log re-recording + docs

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_11.md`) with strict TDD. Tests first (CLI tests
> + a textual_integration test for the startup-replay path), then
> implementation. Run pylint, pytest, mypy via the mandatory MCP tools.
> Single commit.

## WHERE

- Modify: `src/mcp_coder/cli/commands/icoder.py` — rewrite resume
  resolution; trigger startup picker; pass resume `log_path` into
  `ICoderApp`.
- Modify: `src/mcp_coder/cli/parsers.py` — update help text for
  `--continue-session-from` to say `.jsonl`.
- Modify: `src/mcp_coder/icoder/ui/app.py` — accept optional
  `resume_log_path: Path | None`; in `on_mount`, if set, run
  `do_resume(resume_log_path)` **after** `format_runtime_banner` would
  have rendered (the divider+new-banner ordering already lives in
  `do_resume`); and **re-record** replayed events into the current
  event log (fulfils self-contained-logs requirement).
- Modify: `src/mcp_coder/icoder/ui/replay.py` — accept optional
  `event_log: EventLog | None` parameter; when supplied, re-emit each
  event into it.
- Update tests: `tests/icoder/test_cli_icoder.py`,
  `tests/icoder/ui/test_app.py`, `tests/icoder/test_replay.py`
- Modify: `docs/icoder/icoder.md` — document `/load` and the picker.

## WHAT

CLI resume resolution (replaces the existing `args.continue_session_*`
block):

```python
resume_log_path: Path | None = None

if args.session_id:
    resume_session_id = args.session_id
elif args.continue_session_from:
    fp = Path(args.continue_session_from)
    if fp.suffix.lower() == ".json":
        logger.error(
            "--continue-session-from now expects a .jsonl event-log "
            "path, not a response JSON. Refusing to resume."
        )
        return 1
    if fp.suffix.lower() != ".jsonl" or not fp.exists():
        logger.error("Log file not found or not a .jsonl: %s", fp)
        return 1
    resume_log_path = fp
elif args.continue_session:
    summaries = list_icoder_logs(project_dir / "logs", provider=provider)
    if not summaries:
        logger.log(OUTPUT, "No previous sessions in this project.")
    else:
        # Synchronous picker before the main app starts.
        chosen = run_startup_picker(summaries)   # blocks until selection or Esc
        if chosen is not None:
            resume_log_path = chosen
        # else: Esc → fresh session

if resume_log_path is not None:
    resume_session_id = _read_session_id_from_log(resume_log_path)
```

Legacy/unresumable handling: if the user originally ran
`--continue-session-from response.json`, the `.json` branch above
already rejects. If the user passes a `.jsonl` we honour it directly —
the `metadata.log_file_path` indirection is therefore unused on the
icoder CLI. (The metadata field still exists for tooling that wants to
walk back from a response JSON; we simply don't use it here.)

`run_startup_picker(summaries)` is a thin helper that runs a tiny
`App[Optional[Path]]` whose only screen is `SessionPickerScreen`. Its
`on_mount` pushes the picker; the picker dismisses with the chosen
path, the app exits returning that value. Headless-friendly: the helper
takes an optional `app_factory` so tests can substitute a deterministic
selection.

ICoderApp:

```python
def __init__(self, app_core, *, format_tools=True,
             resume_log_path: Path | None = None, **kwargs):
    ...
    self._resume_log_path = resume_log_path

def on_mount(self):
    if self._resume_log_path is not None:
        self.do_resume(self._resume_log_path)
    else:
        # existing live-banner code
        ...
```

`do_resume` (extended): pass `self._core.event_log` into `replay_log`
so replayed events are re-recorded (self-contained logs).

```python
def do_resume(self, log_path: Path) -> None:
    output = self.query_one(OutputLog)
    output.clear(); output.clear_recorded()
    self._core.prepare_for_resume(log_path)        # rotates the event log
    replay_log(self, log_path, event_log=self._core.event_log)
    output.append_text(f"────── Resumed {datetime.now().strftime('%Y-%m-%d %H:%M')} ──────", style="dim")
    output.append_text("\n".join(format_runtime_banner(self._runtime_info_dict())), style="dim")
```

## HOW

- `_read_session_id_from_log(path)` reuses the same lookup as
  `prepare_for_resume` (Step 10). Extracted to a small free function so
  CLI and AppCore share it.
- `run_startup_picker(summaries)` lives in
  `src/mcp_coder/icoder/ui/widgets/session_picker.py` next to the
  screen.
- The `replay_log(app, path, event_log=None)` re-emits each parsed
  event into `event_log` when supplied — this is the
  self-contained-logs requirement made concrete.

## ALGORITHM

```
execute_icoder(args):
    ...
    resume_log_path = resolve_resume_path(args, provider, project_dir)  # may exit 1
    ...
    with EventLog(logs_dir=project_dir/"logs") as event_log:
        event_log.emit("session_start", provider=provider, session_id=session_id, ...)
        ICoderApp(app_core, ..., resume_log_path=resume_log_path).run()
```

```
replay_log(app, path, event_log=None):
    for ev in iter_events(path):
        # render via UI primitives (Step 8)
        ...
        if event_log is not None and ev["event"] != "session_start":
            event_log.emit(ev["event"], **{k: v for k, v in ev.items() if k not in ("event", "t")})
    # session_start IS replayed visually but not re-emitted (the new run
    # already emitted its own session_start at startup)
```

## DATA

- New CLI helper `_read_session_id_from_log(path: Path) -> str | None`.
- `replay_log` extra kwarg: `event_log: EventLog | None = None`.
- `ICoderApp` extra kwarg: `resume_log_path: Path | None = None`.

## Test Cases

1. `--continue-session-from foo.json` → exit code 1; stderr/log
   contains the hard-error message.
2. `--continue-session-from missing.jsonl` → exit code 1.
3. `--continue-session-from real.jsonl` (fixture) → app runs;
   `_read_session_id_from_log` returns the recorded id; `do_resume` is
   triggered.
4. `--continue-session` with no prior logs → message logged; app runs
   without replay.
5. `--continue-session` with prior logs → `run_startup_picker` is
   invoked; if the helper returns a path, the main app runs with
   `resume_log_path` set; if `None`, app runs fresh.
6. `--continue-session-from response.json` (legacy response JSON) →
   hard error, no fallback.
7. (textual_integration) `do_resume` end-to-end: a fixture log with a
   user input + LLM stream is replayed; then the resumed-divider
   appears; then the new banner; the new event log file contains the
   re-recorded events (verify via `iter_events` on the new file).
8. Self-contained: after a resume, the new log file alone is
   sufficient to reproduce the same UI state — i.e. `replay_log` of
   the new file produces the same `output_log.recorded_lines` as the
   original session minus the resume divider sequence.
9. Docs: `docs/icoder/icoder.md` mentions `/load` in the slash-command
   table and includes a brief paragraph on the picker.

## Out of Scope

- `metadata.log_file_path` is now unused by the icoder CLI's resume
  logic. It remains in `store_session()` (Step 3) as a forward-compat
  hook for other tooling. Removing it from `store_session` is a
  separate clean-up if ever desired — **not** in this PR.
