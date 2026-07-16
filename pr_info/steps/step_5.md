# Step 5 — End-to-end threading: `AppCore`, `ui/app.py`, CLI wiring

**Read first:** `pr_info/steps/summary.md` (design changes §3, §5).
**Depends on:** Step 3 (`SendToLLM.allowed_tools`), Step 4 (`stream(allowed_tools=…)`,
`FakeLLMService.last_allowed_tools`, `permission_warning`).

Carry the declared set across the two lossy hops to the service, surface the warning
in the TUI, and wire the enforcement flag from the CLI. This closes the remaining ACs
(field survives `handle_input`; warning reaches both channels).

## WHERE
- `src/mcp_coder/icoder/core/app_core.py` — `handle_input` reconstruction; `stream_llm`.
- `src/mcp_coder/icoder/ui/app.py` — `SendToLLM` case; `_stream_llm`; render guard.
- `src/mcp_coder/cli/commands/icoder.py` — `RealLLMService(...)` call.
- Tests: `tests/icoder/test_app_core.py`, `tests/icoder/test_app_pilot.py`,
  `tests/icoder/test_cli_icoder.py`.

## WHAT / HOW
1. **`app_core.py` — preserve the field** (add `from dataclasses import replace`):
   ```python
   elif isinstance(action, SendToLLM):
       resolved.append(replace(action, text=action.text or text))
   ```
2. **`app_core.py` — forward through the core:**
   ```python
   def stream_llm(self, text: str,
                  allowed_tools: tuple[str, ...] | None = None) -> Iterator[StreamEvent]:
       ...
       for event in self._llm_service.stream(text, allowed_tools):
           ...
   ```
3. **`ui/app.py` — `SendToLLM` case** passes the field into the worker:
   ```python
   case SendToLLM():
       output.write("")
       self.query_one(BusyIndicator).show_busy("Querying LLM...")
       llm_input, allowed = action.text, action.allowed_tools
       self.run_worker(
           lambda llm_input=llm_input, allowed=allowed:
               self._stream_llm(llm_input, allowed),
           thread=True,
       )
   ```
   `_stream_llm(self, text: str, allowed_tools: tuple[str, ...] | None = None)` →
   `for event in self._core.stream_llm(text, allowed_tools):`
4. **`ui/app.py` — render guard** at the top of `_handle_stream_event`
   (before `self._renderer.render(event)`, which would drop the unknown type):
   ```python
   if event.get("type") == "permission_warning":
       self.query_one(OutputLog).append_text(
           str(event.get("message", "")), style=STYLE_CANCELLED)
       return
   ```
   (Event-log half is free: `AppCore.stream_llm` already forwards non-`raw_line`
   events via `emit("stream_event", **event)`.)
5. **`cli/commands/icoder.py`** — add `enforce_skill_tools=False` to the
   `RealLLMService(...)` construction (explicit seam; #1062 flips it later).

## ALGORITHM
_(none — plumbing + one render branch)_

## DATA
- No new types. `permission_warning` renders as a dim-orange line
  (`STYLE_CANCELLED`) in the output log and is auto-logged as a `stream_event`.

## Tests (write first)
- `test_app_core`: `handle_input` on input that a fixture command maps to
  `SendToLLM(text="", allowed_tools=("mcp__srv__a",))` → returned action still has
  `allowed_tools == ("mcp__srv__a",)` **and** `text` resolved to the original input
  (field survives across the reconstruction).
- `test_app_core`: `stream_llm(text, ("mcp__srv__a",))` with a `FakeLLMService` →
  `fake.last_allowed_tools == ("mcp__srv__a",)` (forwarded through the core).
- `test_app_pilot`: submitting input whose command yields `SendToLLM(..., allowed_tools=…)`
  reaches `FakeLLMService.last_allowed_tools` (UI worker threads it).
- `test_app_pilot`: a canned `permission_warning` event renders its message text in the
  output log.
- `test_cli_icoder`: the `RealLLMService` construction is called with
  `enforce_skill_tools=False` (patch/inspect construction, consistent with existing
  CLI tests).

## Definition of done
All three source files threaded; warning renders; CLI wired; the four test files pass;
checks green. One commit.

## LLM prompt
> Implement Step 5 from `pr_info/steps/step_5.md` (context in `pr_info/steps/summary.md`;
> depends on Steps 3–4). Using TDD, first add the listed tests to
> `tests/icoder/test_app_core.py`, `tests/icoder/test_app_pilot.py`, and
> `tests/icoder/test_cli_icoder.py`, then: preserve `SendToLLM.allowed_tools` via
> `dataclasses.replace` in `AppCore.handle_input`; add `allowed_tools` to
> `AppCore.stream_llm` and forward it to the service; pass `action.allowed_tools` through
> the `ui/app.py` `SendToLLM` worker and `_stream_llm`; add the `permission_warning`
> render guard at the top of `_handle_stream_event`; pass `enforce_skill_tools=False` in
> the `cli/commands/icoder.py` `RealLLMService(...)` call. Run pylint, pytest (unit markers
> per CLAUDE.md), and mypy; fix all issues. One commit.
