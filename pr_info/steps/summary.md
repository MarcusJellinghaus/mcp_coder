# iCoder - Initial Setup: Textual TUI with Three-Layer Architecture

## Issue: #617

## Summary

Create a new `mcp-coder icoder` CLI command — an interactive Textual-based TUI for conversational coding with LLMs. The architecture maximizes LLM testability by keeping all logic outside the UI layer via a three-layer design.

## Architectural / Design Decisions

### Three-Layer Architecture

```
src/mcp_coder/icoder/
├── core/           ← All logic (NO Textual imports)
├── ui/             ← Thin Textual shell (minimal logic)
└── services/       ← IO abstractions (LLM wrapper)
```

**Core layer** (`core/`): Plain Python. Owns command registry, input routing, event log. Exposes `handle_input(text) → Response`. Directly testable with pytest — no Textual dependency.

**UI layer** (`ui/`): Textual App with `RichLog` (output) + `TextArea` (input). Translates UI events to `core.handle_input()` calls. Uses `run_worker(thread=True)` + `call_from_thread()` to bridge the sync `prompt_llm_stream()` iterator into the async event loop. Should be "too dumb to have bugs."

**Services layer** (`services/`): Wraps `prompt_llm_stream()` behind a `Protocol`. Tests swap in `FakeLLM` for deterministic, instant responses.

### Key Design Choices

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Command registry | Simple dict + `@register` decorator | 3 commands — no framework needed |
| Session persistence | Reuse existing `llm/storage/` | `find_latest_session()`, `extract_session_id()`, `ResponseAssembler` already exist |
| LLM service | `Protocol` with one `stream()` method | Simpler than ABC, sufficient for DI |
| Types | Minimal dataclasses, no inheritance | `Response(text, clear_output, quit)` + `EventEntry` |
| Event log | Single class: in-memory list + JSONL writer | No event bus / pub-sub |
| Async bridging | `run_worker(thread=True)` + `call_from_thread()` | Sync iterator needs a real thread |
| Error handling | Display in output area, stay alive | User can retry |
| Commands | Separate files per issue spec | `help.py`, `clear.py`, `quit.py` — each ~10 lines |

### Async Bridge Flow

1. User presses Enter → `core.handle_input(text)` determines input goes to LLM
2. `app.run_worker(self._stream_llm, thread=True)` starts a background thread
3. Worker thread calls `prompt_llm_stream()` — blocking iteration
4. For each `StreamEvent`, worker calls `self.app.call_from_thread(post_event_to_ui)`
5. UI updates `RichLog` incrementally from the event loop

## Files Created

### Package structure
```
src/mcp_coder/icoder/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── types.py              # Response, Command, EventEntry dataclasses
│   ├── event_log.py          # EventLog: in-memory + JSONL writer
│   ├── command_registry.py   # CommandRegistry: dict + @register decorator
│   ├── app_core.py           # AppCore: handle_input() → Response
│   └── commands/
│       ├── __init__.py
│       ├── help.py            # /help handler
│       ├── clear.py           # /clear handler
│       └── quit.py            # /quit handler
├── services/
│   ├── __init__.py
│   └── llm_service.py        # LLMService Protocol + RealLLMService + FakeLLMService
└── ui/
    ├── __init__.py
    ├── app.py                 # ICoderApp(App) — wires UI events to core
    ├── styles.py              # CSS string constant
    └── widgets/
        ├── __init__.py
        ├── output_log.py     # OutputLog(RichLog) — scrollable output
        └── input_area.py     # InputArea(TextArea) — Enter=submit, Shift-Enter=newline
```

### Test structure
```
tests/icoder/
├── __init__.py
├── conftest.py               # Shared fixtures (FakeLLM, AppCore factory)
├── test_types.py             # Step 1: dataclass tests
├── test_event_log.py         # Step 2: event log tests
├── test_command_registry.py  # Step 3: registry + command tests
├── test_llm_service.py       # Step 4: LLM service protocol tests
├── test_app_core.py          # Step 5: AppCore routing tests
├── test_cli_icoder.py        # Step 6: CLI parser + wiring tests
├── test_widgets.py           # Step 7: widget unit/integration tests
├── test_app_pilot.py         # Step 8: Textual headless integration tests
└── test_snapshots.py         # Step 9: SVG snapshot tests (Windows-only)
```

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Add `tui` optional-dependency group (`textual`, `textual-dev`); add `pytest-textual-snapshot` in step 9 |
| `src/mcp_coder/cli/parsers.py` | Add `add_icoder_parser()` function |
| `src/mcp_coder/cli/main.py` | Add import + route for `icoder` command |
| `src/mcp_coder/cli/commands/icoder.py` | New: `execute_icoder(args)` command handler |

## Implementation Steps

9 steps, each producing one commit (tests + implementation + checks passing):

1. **Dependencies + package skeleton + types** — Foundation (textual as optional `tui` dependency)
2. **Event log** — Core structured logging (with context manager support)
3. **Command registry + built-in commands** — Slash command infrastructure
4. **LLM service protocol** — Service abstraction layer
5. **AppCore** — Central input routing (wires steps 2-4 together)
6. **CLI wiring** — `mcp-coder icoder` command registration (lazy textual import)
7. **UI widgets** — styles.py, OutputLog, InputArea + widget unit tests
8. **ICoderApp + pilot integration tests** — Textual app shell with async bridging
9. **Snapshot tests** — SVG visual regression (Windows-only)
