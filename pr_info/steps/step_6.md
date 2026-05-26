# Step 6 — `OutputLog` tier model + `toggle_unit_tier` + `rebuild()` + `on_resize`

## Goal

Layer the tier model on top of the registry from step 5:
- Track a global default tier (`compressed` initially) and per-unit overrides.
- Expose `toggle_unit_tier(unit_id)`.
- Extend `_render_unit_atomic` to dispatch on effective tier (oneline vs compressed). The `rebuild()` walk itself does not change — it's already implemented in step 5.
- Wire `on_resize` to call `rebuild()` (wrap-derived ranges invalidate on resize).
- `set_tool_display_default(tier)` updates the default AND wipes per-unit overrides (the `/display` hard reset).

Click handlers and the App layer wire-up come in steps 8 and 9.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/output_log.py` — tier state + methods + rebuild + on_resize
- `src/mcp_coder/llm/formatting/stream_renderer.py` — extract `format_tool_compressed(name, args, output_lines, total_lines, truncated, duration_ms, is_error) -> list[str]` (the `│  …` body lines plus the `└ done/error` footer) alongside `format_tool_start` and `format_tool_oneline`. Explicit-fields signature — no `ToolResult` synthesis. `_render_unit_atomic` (this step) calls this helper directly. Step 9's `_handle_stream_event` ToolResult branch triggers it **indirectly** via `update_unit_and_rerender → rebuild → _render_unit_atomic` (step 9 does NOT call `format_tool_compressed` directly).
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
def format_tool_compressed(
    name: str,
    args: dict[str, object],
    output_lines: tuple[str, ...],
    total_lines: int,
    truncated: bool,
    duration_ms: int | None,
    is_error: bool,
) -> list[str]:
    """Compressed-tier body lines for a completed tool invocation.

    Takes the pre-rendered triple directly (no ToolResult synthesis).
    Returns the `│  …` body lines plus the `└ done` / `└ error` footer
    (matching today's inline rendering in app.py). Pure function.
    """
```

`_render_unit_atomic` (this step, for rebuild) calls this helper directly. Step 9's `_handle_stream_event` ToolResult branch (live streaming) reaches the same helper **indirectly** via `update_unit_and_rerender → rebuild → _render_unit_atomic` — step 9 itself does NOT call `format_tool_compressed`. Callers pass explicit fields; no `ToolResult` synthesis required. This guarantees byte-identical output: both the initial render and any subsequent rebuilds go through the same code path.

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
  - `unit.kind == "tool"`: tier is determined by `_tool_display_default` modified by `_tool_tier_overrides.get(unit.id)`.
    - For `oneline`: call `format_tool_oneline(name=unit.tool_name, args=unit.args, duration_ms=unit.duration_ms, is_error=unit.is_error)`. Return `([oneline], STYLE_TOOL_OUTPUT)`. (Oneline subsumes start + body into one line.)
    - For `compressed`:
      1. **Start lines** — ALWAYS present, via `format_tool_start(...)` from unit fields (`tool_name`, `args`).
      2. **Body lines** — ONLY when `unit.output_lines` is non-empty (i.e., the result has arrived). Append `format_tool_compressed(name=unit.tool_name, args=unit.args or {}, output_lines=unit.output_lines, total_lines=unit.total_lines, truncated=unit.truncated, duration_ms=unit.duration_ms, is_error=unit.is_error)`. If `unit.output_lines` is empty (in-flight tool, no result yet), render start lines only — no `└ done` footer.
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
11. `test_rebuild_with_pending_tool_renders_start_only` — call `append_unit(tool_start_unit, start_lines, ...)` where the unit has `output_lines=()` (in-flight tool, no result yet). `rebuild()` produces only the start lines via `format_tool_start` — the `└ done` footer does NOT appear. Then call `update_unit_and_rerender(uid, output_lines=("a","b"), total_lines=2, truncated=False, duration_ms=42, is_error=False)` → `rendered_lines` now contains both start lines AND the `└ done (2 lines, 42ms)` footer.

Tests in `tests/llm/formatting/test_stream_renderer.py`:

12. `test_format_tool_compressed_done` — pass `output_lines=("a","b")`, `total_lines=2`, `duration_ms=120`, `is_error=False` → body lines start with `│  ` and footer is `└ done (2 lines, 120ms)`.
13. `test_format_tool_compressed_error` — `is_error=True` → footer is `└ error`.
14. `test_format_tool_compressed_empty_output` — `output_lines=()`, `total_lines=0` → only footer line returned.

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
> - Extract `format_tool_compressed(name, args, output_lines, total_lines, truncated, duration_ms, is_error) -> list[str]` into `stream_renderer.py` alongside `format_tool_start` and `format_tool_oneline`. Explicit-fields signature — no `ToolResult` synthesis required by callers. `_render_unit_atomic` (this step) calls it directly. Step 9's live `tool_result` branch reaches it **indirectly** via `update_unit_and_rerender → rebuild → _render_unit_atomic` — single source of truth for compressed-tier body output.
> - `_render_unit_atomic` for tool kind: start lines always; body lines only when `unit.output_lines` is non-empty.
> - TDD: 14 test cases first (11 output_log + 3 stream_renderer), then implement.
>
> All three quality gates green after the change.
