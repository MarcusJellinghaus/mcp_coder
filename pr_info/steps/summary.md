# Issue #629 — Tiered Tool Display + Detail Modal + Response Refactor

## Goal

Two stacked deliverables in one PR:

1. **Response refactor** — convert `Response` from boolean flag-bag to typed-action list (`Response.actions: tuple[Action, ...]`). Mechanical, behavior-preserving.
2. **Tiered tool display + detail modal** — keep `OutputLog` as `RichLog`; add a sidecar `(start, end) → unit_id` registry. Tool blocks toggle between tier‑1 oneline ↔ tier‑2 compressed on left single click; any content unit opens a tier‑3 `DetailModal` (`TextArea(read_only=True)`) on double click or `F2`. New `/display` slash command + `--tool-display` CLI flag set the global default.

Depends on #617.

## Simplifications adopted (vs. issue's original decisions)

These preserve all issue requirements while reducing complexity:

| Simplification | Rationale |
|---|---|
| **Disjoint ranges + "first containing range wins"** | Ranges are disjoint by design (turn has gaps where tools sit). "First match" gives same result as "smallest match" but is simpler. |
| **Per‑unit tier overrides as a separate dict, not a mutable field on `ContentUnit`** | `ContentUnit` stays `frozen=True`; `/display` hard-reset = one-line dict clear. |
| **`_units` is a single `dict`** (insertion-ordered) | Python dicts preserve order — no separate `_order: list` needed. |
| **Drop `RebuildOutput` from Phase A** | Only used in Phase B; adding earlier is dead code. |
| **`SendToLLM` carries the resolved text** | `AppCore.handle_input` resolves `llm_text or text`; UI dispatch site has one path. |
| **Render script preserves interleaving** | `_script: list[(unit_id, line\|None)]` captures the actual write order (turn text lines interleaved with tools). Rebuild walks the script; no multi-range merging logic. |

## Architectural / design changes

### Phase A — `Response` refactor

`core/types.py` gains a typed-action union. Each existing boolean field on `Response` maps to one action class. UI dispatch becomes a `match` over `response.actions`.

```python
Action = Quit | ClearOutput | OpenPicker | ResetSession | SendToLLM | OutputText
Response.actions: tuple[Action, ...] = ()
```

Mirrors the existing `RenderAction` pattern in `llm/formatting/render_actions.py`. `RebuildOutput` action is added in step 10 when `/display` lands.

### Phase B — tier display data model

```
ContentUnit  (frozen dataclass)
  id, kind, timestamp, tool_name, args, output, duration_ms, is_error, full_text, parent_id

OutputLog state additions:
  _units:        dict[str, ContentUnit]              # insertion-ordered
  _script:       list[tuple[str, str | None]]        # (unit_id, line | None for atomic)
  _ranges:       list[tuple[int, int, str]]          # (start, end, unit_id)
  _screen_lines: list[str]                           # current rendered screen state
  _tool_display_default:   Literal["oneline","compressed"]
  _tool_tier_overrides:    dict[str, Literal["oneline","compressed"]]
```

`_recorded` (existing) stays append-only — survives toggles. `_screen_lines` (new) reflects the current display; recomputed on every rebuild.

Two distinct entry points on `OutputLog`:
- `append_text(text, style=...)` — unchanged behavior; banners/markers/spacers stay on this path.
- `append_unit(unit)` / `extend_open_unit(unit_id, lines)` / `finalize_open_unit(unit_id)` — registers a clickable unit.

**`last_unit()` semantics**: returns the most recent value in `_units` by dict insertion order. After a mid-turn tool fires, the tool is the most recent unit; `F2` then opens the tool's modal, not the still-streaming assistant turn. This is intentional.

### Detail modal

New widget: `DetailModal(ModalScreen)` containing `TextArea(read_only=True)`. Closes on `Escape` / `Enter`. `Ctrl+C` overrides the app-level no-op binding (`priority=True`) to copy selection. Layout: header / args / output / footer (or kind / text / footer for non-tool units).

### Renderer FIFO + cleanup

`StreamEventRenderer` becomes stateful. New `_pending: deque[tuple[name, monotonic_start]]`. On `tool_use_start` push; on `tool_result` pop matching name, compute `duration_ms`. New `cleanup_pending() -> list[ToolResult]` synthesizes cancelled results for orphans (called on cancel and on `StreamDone`). Class docstring updated.

### Provider edits

Add `is_error: bool` to the `tool_result` event in:
- `claude_code_cli_streaming.py` — read from `block["is_error"]`
- `copilot_cli_streaming.py` — derive from `tool.execution_complete` status
- `langchain/agent.py` — detect tool errors via `on_tool_end`'s `data.output` (`ToolMessage` with `status == 'error'`) and emit `tool_result` with `is_error=True`

Add `is_error: bool = False` to `ToolResult` render-action.

### Click translation + F2

`OutputLog.on_click`: left button only; `chain == 1` debounced (~250 ms) → `toggle_unit_tier()`; `chain == 2` → `app.push_screen(DetailModal(unit))`; `chain >= 3` ignored. `on_resize` → `rebuild()` (handles wrap shifts).

`ICoderApp` adds `F2` binding → opens modal for `output.last_unit()` (silent no-op if none).

### `/display` command

New `core/commands/display.py`. Accepts `oneline` / `compressed`. Updates `AppCore.tool_display`. Returns `Response(actions=(RebuildOutput(),))`. `OutputLog.set_tool_display_default()` updates the default AND wipes `_tool_tier_overrides` (the "hard reset"). CLI flag `--tool-display=oneline|compressed` plumbs initial value.

## Files created or modified

### New files

| Path | Purpose |
|---|---|
| `src/mcp_coder/icoder/ui/widgets/detail_modal.py` | `DetailModal(ModalScreen)` with `TextArea(read_only=True)` |
| `src/mcp_coder/icoder/core/commands/display.py` | `/display oneline|compressed` slash command |
| `tests/icoder/ui/test_detail_modal.py` | Modal text content, escape/enter close, Ctrl+C copy |
| `tests/icoder/test_display_command.py` | Slash-command dispatch + hard-reset semantics |

### Modified files

| Path | Change |
|---|---|
| `src/mcp_coder/icoder/core/types.py` | Typed `Action` union; `Response.actions` |
| `src/mcp_coder/icoder/core/commands/{help,clear,quit,color,info,load}.py` | Return `Response(actions=(...,))` |
| `src/mcp_coder/icoder/core/commands/__init__.py` | Register `/display` |
| `src/mcp_coder/icoder/core/command_registry.py` | Thread `app_core` so `/display` can capture it |
| `src/mcp_coder/icoder/core/app_core.py` | `tool_display` field; `handle_input` returns typed actions; `SendToLLM(text=resolved)` |
| `src/mcp_coder/icoder/ui/app.py` | `match` dispatch over actions; migrate user-input/tool/assistant-turn writes to `append_unit`/`extend_open_unit`; orphan cleanup; `F2` binding; `on_resize` |
| `src/mcp_coder/icoder/ui/replay.py` | No source changes (delegates to `_handle_stream_event` + `append_text`); migrates "for free" once App migrates |
| `src/mcp_coder/icoder/ui/widgets/output_log.py` | `ContentUnit` (incl. `parent_id`), registry state, `append_unit`/`extend_open_unit` (raises for tools)/`finalize_open_unit`/`update_unit_and_rerender`, `unit_at_line`, `last_unit`, `toggle_unit_tier`, `rebuild`, `set_tool_display_default`, `on_click`, `on_resize`, `rendered_lines`; `clear_recorded` renamed to `clear_state` (also wipes `_tool_tier_overrides`) |
| `src/mcp_coder/llm/formatting/render_actions.py` | `ToolResult.is_error: bool = False` |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | `format_tool_oneline()`; `format_tool_compressed()`; `StreamEventRenderer` FIFO + `cleanup_pending()`; class docstring update |
| `src/mcp_coder/llm/types.py` | `StreamEvent` docstring documents `is_error` on `tool_result` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Propagate `is_error` from `tool_use_result` block |
| `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` | Propagate `is_error` from `tool.execution_complete` status |
| `src/mcp_coder/llm/providers/langchain/agent.py` | Detect tool errors via `on_tool_end`'s `data.output` (`ToolMessage` with `status == 'error'`) and emit `tool_result(is_error=True)` instead of raising |
| `src/mcp_coder/cli/parsers.py` | `--tool-display` option in `add_icoder_parser` |
| `src/mcp_coder/cli/commands/icoder.py` | Thread `--tool-display` to `AppCore` |
| `tests/icoder/test_types.py` | Tests for typed-action shape |
| `tests/icoder/test_app_core.py` | Update for new `handle_input` return shape |
| `tests/icoder/test_*_command.py` | Update assertions to typed actions |
| `tests/icoder/ui/test_output_log.py` | New tests for registry / tiering / rebuild; existing tests audited (emission → `recorded_lines`, screen state → `rendered_lines`) |
| `tests/icoder/test_app_pilot.py` | Click / double-click / chain-3 / right-button / F2 / resize via Pilot |
| `tests/llm/formatting/test_stream_renderer.py` | `format_tool_oneline`; FIFO pairing; orphan cleanup |
| `tests/llm/providers/{claude,copilot,langchain}/*` | `is_error` round-trip per provider |
| `tests/icoder/test_snapshots.py` | 3 new snapshots: default tier, after `/display oneline`, modal-over-tool |
| `tests/icoder/test_cli_icoder_parser.py` | `--tool-display` arg |
| `docs/icoder/icoder.md` | Tier-display section; `/display` row; F2 in shortcuts |

## Steps overview

| # | Title | Touches |
|---|---|---|
| 1 | `Response` refactor → typed actions | `core/types.py`, 6 command files, `app_core.py`, `app.py`, tests |
| 2 | `is_error` propagation across providers + `ToolResult.is_error` | 3 streaming files, `render_actions.py`, `llm/types.py`, tests |
| 3 | `format_tool_oneline()` pure function | `stream_renderer.py`, tests |
| 4 | `StreamEventRenderer` FIFO + `cleanup_pending()` | `stream_renderer.py`, tests |
| 5 | `OutputLog` registry data layer | `output_log.py`, tests (audit + new) |
| 6 | `OutputLog` tier model + `rebuild()` + `on_resize` | `output_log.py`, tests |
| 7 | `DetailModal` widget | `detail_modal.py` (new), tests |
| 8 | Click handler + `F2` binding | `output_log.py`, `app.py`, tests |
| 9 | `ICoderApp` migrates to `append_unit` flow; orphan cleanup | `app.py`, tests (Pilot + replay) |
| 10 | `/display` + `--tool-display` + `RebuildOutput` action + `/help` | `display.py` (new), `parsers.py`, `icoder.py` CLI, `app_core.py`, `types.py`, `help.py`, `docs/icoder/icoder.md`, tests |

After each step: all three checks (pylint, pytest, mypy) must be green.
