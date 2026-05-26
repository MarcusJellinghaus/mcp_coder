# Step 1 — `Response` refactor to typed actions

## Goal

Convert `Response` from a flag-bag dataclass to a tuple of typed action dataclasses, mirroring the `RenderAction` pattern in `llm/formatting/render_actions.py`. Mechanical, behavior-preserving — no UI changes visible to the user.

## WHERE

- `src/mcp_coder/icoder/core/types.py` — add Action union, refactor `Response`
- `src/mcp_coder/icoder/core/commands/{help,clear,quit,color,info,load}.py` — return typed actions
- `src/mcp_coder/icoder/core/app_core.py` — emit per-action events; return typed actions
- `src/mcp_coder/icoder/ui/app.py` — replace if/elif dispatch with `match` over `response.actions`
- `tests/icoder/test_types.py` — Action shape tests
- `tests/icoder/test_app_core.py` — update return-shape assertions
- `tests/icoder/test_*_command.py` (help, clear, quit, color, info, load) — update assertions

## WHAT

```python
# core/types.py
@dataclass(frozen=True)
class Quit: pass

@dataclass(frozen=True)
class ClearOutput: pass

@dataclass(frozen=True)
class OpenPicker: pass

@dataclass(frozen=True)
class ResetSession: pass

@dataclass(frozen=True)
class SendToLLM:
    text: str

@dataclass(frozen=True)
class OutputText:
    text: str

Action = Quit | ClearOutput | OpenPicker | ResetSession | SendToLLM | OutputText

@dataclass(frozen=True)
class Response:
    actions: tuple[Action, ...] = ()
```

Each command now returns `Response(actions=(...,))`:

| Command | Old | New |
|---|---|---|
| `/help` | `Response(text=...)` | `Response(actions=(OutputText(text=...),))` |
| `/clear` | `Response(clear_output=True, reset_session=True)` | `Response(actions=(ClearOutput(), ResetSession()))` |
| `/quit` / `/exit` | `Response(quit=True)` | `Response(actions=(Quit(),))` |
| `/color` (success) | `Response()` | `Response(actions=())` |
| `/color` (error) | `Response(text=msg)` | `Response(actions=(OutputText(text=msg),))` |
| `/info` | `Response(text=info)` | `Response(actions=(OutputText(text=info),))` |
| `/load` | `Response(open_picker=True)` | `Response(actions=(OpenPicker(),))` |

`AppCore.handle_input()`:
- non-empty non-command input → `Response(actions=(SendToLLM(text=text),))`
- empty input → `Response()` (unchanged)
- command dispatch → returns whatever the command returns; if any action is `ResetSession`, run the existing rotate/emit logic; if any is `OutputText`, emit `output_emitted` for its text

## HOW

- Keep the `output_emitted` event emission in `AppCore.handle_input()` driven by iteration over `response.actions` (check for `OutputText`), not by a bare `response.text` access.
- `ResetSession` handling stays in `AppCore.handle_input()` (rotate event log + emit session_start) — triggered when `ResetSession()` is in `response.actions`.
- Empty `Response(actions=())` is the new "do nothing" sentinel — replaces today's `Response()`. Document this in the dataclass docstring.
- Ordering: `AppCore.handle_input` performs all state-mutation side effects (rotate event log, emit session_start, color updates) BEFORE returning the typed `Response`. The UI then iterates `response.actions` strictly in tuple order. `case ResetSession(): pass` is a marker case for symmetry with the typed union — the actual reset already happened inside `AppCore`.
- UI dispatch in `app.py:on_input_area_input_submitted` becomes:

```python
for action in response.actions:
    match action:
        case Quit():            self.exit()
        case ClearOutput():     output.clear(); output.clear_state()  # see step 5 for the rename
        case OpenPicker():      self.open_picker_for_load()
        case OutputText(t):     output.append_text(t)
        case SendToLLM(t):
            output.write("")
            self.query_one(BusyIndicator).show_busy("Querying LLM...")
            self.run_worker(lambda t=t: self._stream_llm(t), thread=True)
        case ResetSession():    pass  # already handled by AppCore
```

## ALGORITHM (handle_input)

```
text = text.strip()
if not text: return Response()
emit("input_received", text=text)
response = registry.dispatch(text)
if response is not None:
    emit("command_matched", command=...)
    for action in response.actions:
        if isinstance(action, OutputText): emit("output_emitted", text=action.text)
        if isinstance(action, ResetSession): reset_session(); rotate(); emit_session_start()
    return response
return Response(actions=(SendToLLM(text=text),))
```

## DATA

- `Response.actions` is a tuple of `Action` instances (frozen dataclasses). Empty tuple means "no action".
- Order in the tuple defines dispatch order.

## TDD

Write tests first:

1. `tests/icoder/test_types.py::test_response_default_empty_actions` — `Response().actions == ()`
2. `tests/icoder/test_types.py::test_response_with_actions_frozen` — instances are hashable and immutable
3. `tests/icoder/test_app_core.py::test_handle_input_empty_returns_empty_response` — unchanged
4. `tests/icoder/test_app_core.py::test_handle_input_text_returns_send_to_llm_action`
5. `tests/icoder/test_app_core.py::test_handle_input_clear_returns_clear_then_reset_session_actions`
6. Per-command tests: assert each handler returns `Response(actions=(<expected>,))`

Then implement.

## Code quality gates

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check (extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

All three must be green.

## LLM Prompt

> Implement **Step 1** from `pr_info/steps/step_1.md` (refactor `Response` to typed-action list).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Mechanical refactor only — no behavior change is visible to the user.
> - Frozen dataclasses; `Response.actions` is `tuple[Action, ...]`.
> - Follow TDD: update / add tests first, then implement.
> - Match the patterns used in `llm/formatting/render_actions.py`.
> - `RebuildOutput` action is **not** in this step (lands in step 10).
>
> After the change, all three quality gates (pylint, pytest, mypy) must pass.
