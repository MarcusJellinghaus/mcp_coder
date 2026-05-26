# Step 6 — `OutputLog` tier model + `toggle_unit_tier` + `rebuild()` + `on_resize`

## Goal

Layer the tier model on top of the registry from step 5:
- Track a global default tier (`compressed` initially) and per-unit overrides.
- Expose `toggle_unit_tier(unit_id)` and `rebuild()`.
- Wire `on_resize` to call `rebuild()` (wrap-derived ranges invalidate on resize).
- `set_tool_display_default(tier)` updates the default AND wipes per-unit overrides (the `/display` hard reset).

Click handlers and the App layer wire-up come in steps 8 and 9.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/output_log.py` — tier state + methods + rebuild + on_resize
- `src/mcp_coder/llm/formatting/stream_renderer.py` — extract `format_tool_compressed(start, result) -> list[str]` (the `│  …` body lines plus the `└ done/error` footer) alongside `format_tool_start` and `format_tool_oneline`. Both `_render_unit_atomic` (this step) and step 9's `_handle_stream_event` ToolResult branch call this helper.
- `tests/icoder/ui/test_output_log.py` — tier and rebuild tests
- `tests/llm/formatting/test_stream_renderer.py` — tests for `format_tool_compressed`

## WHAT

```python
class OutputLog(RichLog):
    _tool_display_default: Literal["oneline", "compressed"] = "compressed"
    _tool_tier_overrides:  dict[str, Literal["oneline", "compressed"]] = {}

    def effective_tier(self, unit_id: str) -> Literal["oneline", "compressed"]
    def toggle_unit_tier(self, unit_id: str) -> Literal["oneline", "compressed"]
    def set_tool_display_default(self, tier: Literal["oneline", "compressed"]) -> None
    def rebuild(self) -> None
    def on_resize(self, event: object) -> None        # textual hook
```

Internal helpers:

```python
def _render_unit_atomic(self, unit: ContentUnit) -> tuple[list[str], str | None]
    # tool → tier-aware rendering (oneline OR compressed); returns (lines, style)
    # user_input → ([f"> {unit.full_text}"], STYLE_USER_INPUT)
```

New shared formatter (in `stream_renderer.py`):

```python
def format_tool_compressed(start: ToolStart, result: ToolResult) -> list[str]:
    """Compressed-tier body lines for a completed tool invocation.

    Returns the `│  …` body lines plus the `└ done` / `└ error` footer
    (matching today's inline rendering in app.py). Pure function.
    """
```

Both `_render_unit_atomic` (this step, for rebuild) and step 9's `_handle_stream_event` ToolResult branch (live streaming) call this helper. This guarantees byte-identical output across both paths.

Style constants (STYLE_USER_INPUT, STYLE_TOOL_OUTPUT, STYLE_CANCELLED) currently live in `app.py`. Keep them there but **import from `app.py` is fine** OR copy the constants into `output_log.py` (cleaner). Recommend copy: define them in `output_log.py` and have `app.py` import them.

## HOW

- `effective_tier(unit_id)` → `_tool_tier_overrides.get(unit_id, _tool_display_default)`.
- `toggle_unit_tier(unit_id)`:
  1. Look up unit; assert `unit.kind == "tool"` (only tools toggle).
  2. Flip: new tier = `"oneline" if effective_tier(uid) == "compressed" else "compressed"`.
  3. Store in `_tool_tier_overrides[unit_id] = new_tier`.
  4. Call `self.rebuild()`.
  5. Return new tier (so callers / events know).
- `set_tool_display_default(tier)`:
  1. `_tool_display_default = tier`.
  2. `_tool_tier_overrides.clear()` — hard reset.
  3. Call `self.rebuild()`.
- `rebuild()`:
  1. Snapshot `_script` and `_units` references.
  2. `super().clear()` (clears RichLog buffer).
  3. Reset `_ranges = []`, `_screen_lines = []`.
  4. Walk script in order; for each entry call `_write_script_entry(...)` which re-uses the same write+measure logic as steps 5's `append_unit` / `extend_open_unit`. Do NOT touch `_recorded`.
- `on_resize`: call `self.rebuild()`. Idempotent — running twice is safe (script and units unchanged). The startup banner that uses `append_text` is unaffected (banner has no unit).
- `_render_unit_atomic(unit)`:
  - `unit.kind == "tool"`: tier is determined by `_tool_display_default` modified by `_tool_tier_overrides.get(unit.id)`. Build the lines as:
    1. **Start lines** — ALWAYS present (from `format_tool_start(...)`).
    2. **Body lines** — ONLY present when `unit.output` is not `None` (i.e., the result has arrived). Source the body from `format_tool_compressed(start, result)` (when effective tier is `compressed`) or just append the oneline metric suffix to the single line (when effective tier is `oneline`).
    - For `oneline`: synthesize a `ToolStart`/`ToolResult` pair from unit fields and call `format_tool_oneline(...)`. Return `([oneline], STYLE_TOOL_OUTPUT)`. (Oneline subsumes start + body into one line.)
    - For `compressed`: emit `format_tool_start(...)` lines; if `unit.output` is set, also emit `format_tool_compressed(start, result)` lines (the `│  …` body + `└ done`/`└ error` footer).
  - `unit.kind == "user_input"`: `([f"> {unit.full_text}"], STYLE_USER_INPUT)`.
  - `unit.kind == "assistant_turn"`: never called (turn content arrives as `(unit_id, line)` script entries, not atomic).

## ALGORITHM (rebuild)

```
script = list(self._script)        # snapshot
self._ranges.clear()
self._screen_lines.clear()
super().clear()                    # clears RichLog buffer (self.lines)

for (unit_id, line) in script:
    unit = self._units[unit_id]
    if line is None:
        lines, style = self._render_unit_atomic(unit)
    else:
        lines, style = [line], None   # turn text line: plain style
    buf_start = len(self.lines)
    for ln in lines:
        self._screen_lines.append(ln)
        if style: super().write(Text(ln, style=style))
        else:     super().write(ln)
    buf_end = len(self.lines)
    self._ranges.append((buf_start, buf_end, unit_id))
```

## DATA

- `_tool_display_default` default at `__init__`: `"compressed"`.
- `_tool_tier_overrides` only gets entries on explicit toggle.
- `toggle_unit_tier` returns the new tier string.

## TDD

Tests in `tests/icoder/ui/test_output_log.py`:

1. `test_effective_tier_defaults_to_compressed`
2. `test_toggle_unit_tier_flips_state` — append tool unit, toggle → `effective_tier == "oneline"`, toggle again → `"compressed"`.
3. `test_toggle_unit_tier_non_tool_raises_or_noops` — try toggling a `user_input` unit → defined behavior (assert ValueError or silent no-op; pick one and document).
4. `test_rebuild_is_idempotent` — append units, capture `_ranges`; `rebuild()`; capture; `rebuild()` again; ranges identical.
5. `test_rebuild_after_toggle_renders_new_tier` — append tool; toggle to oneline; `rebuild()`; `rendered_lines` shows the oneline output (one line) instead of the compressed block.
6. `test_set_tool_display_default_wipes_overrides` — toggle 2 tools to oneline; call `set_tool_display_default("compressed")`; both tools back to compressed in `rendered_lines`.
7. `test_set_tool_display_default_triggers_rebuild` — verify `rendered_lines` actually changed after the call (not just state).
8. `test_on_resize_triggers_rebuild` — append unit; capture rendered_lines; fire `Resize` event; rendered_lines unchanged (same content, ranges may differ if wrap changed).
9. `test_rebuild_does_not_mutate_recorded` — capture `recorded_lines`; `rebuild()`; `recorded_lines` unchanged.
10. `test_toggle_for_assistant_turn_unit_noop_or_raise` — toggle on a turn unit → defined (assert chosen behavior).

Tests in `tests/llm/formatting/test_stream_renderer.py`:

11. `test_format_tool_compressed_done` — start + result with output → body lines start with `│  ` and footer is `└ done (N lines, …ms)`.
12. `test_format_tool_compressed_error` — `is_error=True` → footer is `└ error`.
13. `test_format_tool_compressed_empty_output` — empty output → only footer line returned.

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 6** from `pr_info/steps/step_6.md` (tier model + rebuild + on_resize).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Tier overrides live on `OutputLog`, NOT on `ContentUnit` (which stays `frozen=True`).
> - `set_tool_display_default()` is the `/display` hard reset — updates default AND wipes overrides.
> - `rebuild()` must be idempotent.
> - `_recorded` is never touched by `rebuild()`.
> - Extract `format_tool_compressed(start, result) -> list[str]` into `stream_renderer.py` alongside `format_tool_start` and `format_tool_oneline`. Both the live streaming path (step 9) and `_render_unit_atomic` (this step) call it — single source of truth for compressed-tier body output.
> - `_render_unit_atomic` for tool kind: start lines always; body lines only when `unit.output is not None`.
> - TDD: 13 test cases first (10 output_log + 3 stream_renderer), then implement.
>
> All three quality gates green after the change.
