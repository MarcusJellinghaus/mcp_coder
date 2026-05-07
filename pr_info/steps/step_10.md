# Step 10 — `/load` command + `AppCore.prepare_for_resume()` + `ICoderApp.do_resume()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_10.md`) with strict TDD. Tests first, then code.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Create: `src/mcp_coder/icoder/core/commands/load.py`
- Modify: `src/mcp_coder/icoder/core/command_registry.py` — register `/load`
- Modify: `src/mcp_coder/icoder/core/types.py` — add `open_picker: bool = False`
  to `Response`
- Modify: `src/mcp_coder/icoder/core/app_core.py` — add `prepare_for_resume`
- Modify: `src/mcp_coder/icoder/ui/app.py` — add `do_resume` and
  `open_picker_for_load` handlers
- Create tests: `tests/icoder/test_load_command.py`
- Update tests: `tests/icoder/test_app_core.py`,
  `tests/icoder/ui/test_app.py`

## WHAT

```python
# core/types.py
@dataclass(frozen=True)
class Response:
    ...
    open_picker: bool = False    # NEW — UI should open SessionPickerScreen

# core/commands/load.py
def register_load(registry: CommandRegistry) -> None:
    @registry.register("/load", "Choose and resume a previous session")
    def handle_load(args: list[str]) -> Response:
        return Response(open_picker=True)

# core/app_core.py
def prepare_for_resume(self, log_path: Path) -> str | None:
    """Read session_id from the log's session_start, set it on the LLM
    service, rotate the event log so the new conversation gets a fresh
    file. Returns the resolved session_id (or None if absent)."""

# ui/app.py
def do_resume(self, log_path: Path) -> None:
    """Clear screen, prepare_for_resume, replay_log, render Resumed
    divider, render current banner."""
```

## HOW

- The handler returns `Response(open_picker=True)`; UI sees this in
  `on_input_area_input_submitted`, lists logs (`list_icoder_logs(...)`),
  and pushes a `SessionPickerScreen` via `push_screen` with a callback.
- Callback signature: `(path: Path | None) -> None`.
  - `None` → return to current session unchanged (no-op; refocus input).
  - `Path` → call `app.do_resume(path)`.
- `prepare_for_resume`:
  1. Find the first event with `event == "session_start"` via
     `iter_events(log_path)`; read its `session_id` (the recorded
     conversation key — note this is the **original CLI** `session_id`
     from when the log was written, which may not be a Claude-issued
     id; Claude rotates per turn but the file contains whatever was
     emitted at session start).
  2. Call `self._llm_service.set_session_id(session_id)`.
  3. Call `self._event_log.rotate()`.
  4. Return the session_id string (or `None`).
- `do_resume`:
  1. `output.clear(); output.clear_recorded()`
  2. `app_core.prepare_for_resume(path)`
  3. `replay_log(self, path)` (Step 8)
  4. `output.append_text(f"────── Resumed {now_local} ──────", style="dim")`
  5. Render the live banner (re-using the helper from Step 6).
- The picker uses the **current run's** `runtime_info.project_dir`
  joined with `logs/` as the scan dir (decision #22).

## ALGORITHM

```
on_input_area_input_submitted(message):
    ...
    if response.open_picker:
        logs_dir = Path(self._project_dir) / "logs"
        summaries = list_icoder_logs(logs_dir, provider=self._core.llm_service.provider)
        if not summaries:
            output.append_text("No previous sessions in this project.")
            return
        def callback(selected: Path | None):
            if selected is not None:
                self.do_resume(selected)
        self.push_screen(SessionPickerScreen(summaries), callback)
        return
    ...

prepare_for_resume(log_path):
    session_id = None
    for ev in iter_events(log_path):
        if ev["event"] == "session_start":
            session_id = ev.get("session_id")  # may be None when not recorded
            break
    self._llm_service.set_session_id(session_id)
    self._event_log.rotate()
    return session_id
```

> NOTE: `session_start` payloads written **after Step 2** do not yet
> contain `session_id` because the recorded event has only environment
> data. This step reads `session_id` from a yet-to-be-added field.
> **Add `session_id` (current `args.session_id` value) to the
> `session_start` emit in `cli/commands/icoder.py` as part of this
> step.** When `session_id` is `None` at session start (fresh
> conversation), the field is omitted from the payload, and resume
> falls back to looking at the most recent `stream_event{type=done}`
> in the log for its `session_id` field. Both lookups happen inside
> `prepare_for_resume`.

## DATA

- `Response.open_picker: bool` — new field.
- `LLMService.session_id` may now be set from a non-recent log file's
  recorded id.

## Test Cases

1. `/load` returns `Response(open_picker=True)`; no other side effects.
2. `prepare_for_resume`: with a fixture log containing a
   `session_start{session_id="abc"}`, the LLM service's `session_id`
   becomes `"abc"` and the event log is rotated.
3. `prepare_for_resume`: log lacking `session_start.session_id` but
   containing a `stream_event{type="done", session_id="xyz"}` →
   resolves `"xyz"`.
4. `prepare_for_resume`: log with neither → resolves `None` (caller
   decides whether to refuse — Step 11).
5. `do_resume` (textual_integration): clears the output, replays a
   fixture log, then renders the Resumed divider and current banner in
   that order.
6. `/load` with empty logs dir → user-visible message and no picker is
   pushed.
7. `/load` then Esc on the picker → no state change (session_id, log
   path, output unchanged).

## Out of Scope

- `--continue-session` startup flow — Step 11.
- Hard-error `--continue-session-from .json` handling — Step 11.
