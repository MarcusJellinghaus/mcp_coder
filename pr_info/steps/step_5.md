# Step 5 — `OutputLog` registry data layer

## Goal

Add the sidecar `(start, end) → unit_id` registry and the `append_unit` / `extend_open_unit` / `finalize_open_unit` / `unit_at_line` / `last_unit` / `rendered_lines` API. A minimal `rebuild()` (non-tier — tools always render compressed) ships here so `update_unit_and_rerender` is functional in step 5; step 6 then layers the **tier model and toggle** on top.

Existing `append_text()` semantics unchanged. Banners, spacers, "Resumed" divider, cancelled marker all keep using `append_text()`.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/output_log.py` — `ContentUnit` dataclass + new state + methods
- `src/mcp_coder/llm/formatting/stream_renderer.py` — extract `format_tool_compressed(...)` helper (first home of the helper; step 6 only consumes it)
- `tests/icoder/ui/test_output_log.py` — new tests; **audit existing tests** asserting on `recorded_lines`
- `tests/llm/formatting/test_stream_renderer.py` — new tests for `format_tool_compressed`

## WHAT

```python
@dataclass(frozen=True)
class ContentUnit:
    id: str
    kind: Literal["tool", "user_input", "assistant_turn"]
    timestamp: datetime
    full_text: str = ""
    # tool-only (None / empty defaults for non-tool kinds):
    tool_name: str | None = None
    args: dict[str, object] | None = None
    output: str | None = None             # FULL untruncated output (for the modal, tier 3)
    output_lines: tuple[str, ...] = ()    # NEW — pre-rendered, already-truncated body lines (tier 2)
    total_lines: int = 0                  # NEW — total line count (drives `(N lines, …ms)` footer)
    truncated: bool = False               # NEW — whether head/tail truncation kicked in
    duration_ms: int | None = None
    is_error: bool = False
    # always None in v1 — reserved for v2 nesting per issue #629 Decision
    parent_id: str | None = None

class OutputLog(RichLog):
    # existing _recorded stays as APPEND HISTORY (never rebuilt)
    _units: dict[str, ContentUnit]                    # insertion-ordered
    _script: list[tuple[str, str | None]]             # (unit_id, line | None)
    _ranges: list[tuple[int, int, str]]               # (start, end, unit_id)
    _screen_lines: list[str]                          # current screen state
    _tool_tier_overrides: dict[str, Literal["oneline", "compressed"]] = field(default_factory=dict)
    # Introduced empty in step 5 so `clear_state()` can wipe it.
    # Populated by step 6's `toggle_unit_tier()` and `set_tool_display_default()`.
    # Step 5 does NOT add `_tool_display_default` — that field is introduced by step 6.

    def append_unit(self, unit: ContentUnit, lines: list[str], style: str | None = None) -> None
    def extend_open_unit(self, unit_id: str, lines: list[str], style: str | None = None) -> None
        # raises ValueError if unit.kind == "tool" — tools never extend.
    def finalize_open_unit(self, unit_id: str) -> None      # no-op marker (see HOW)
    def update_unit_and_rerender(self, unit_id: str, **fields: object) -> ContentUnit
        # rebuilds the unit via dataclasses.replace, writes it back to _units, then rebuild().
    def unit_at_line(self, line: int) -> ContentUnit | None
    def last_unit(self) -> ContentUnit | None
    @property
    def rendered_lines(self) -> list[str]
    def clear_state(self) -> None                     # NEW (renamed from clear_recorded): wipes _recorded/_units/_script/_ranges/_screen_lines/_tool_tier_overrides
```

Add a one-line code comment at `__init__` noting `max_lines` must remain `None` (eviction would invalidate `_ranges`).

**Note on tool fields:** the pre-rendered triple (`output_lines`, `total_lines`, `truncated`) is populated once at `tool_result` time (step 9) and read by `_render_unit_atomic`; the full `output` field is reserved for the modal's tier-3 view (step 7).

**Extracted helper:** this step also extracts `format_tool_compressed(name: str, args: dict, output_lines: tuple[str, ...], total_lines: int, truncated: bool, duration_ms: int | None, is_error: bool) -> list[str]` from `app.py`'s current inline rendering of tool result bodies (the `│  …` body lines plus the `└ done` / `└ error` footer) into `src/mcp_coder/llm/formatting/stream_renderer.py`, alongside the existing `format_tool_start` / `format_tool_oneline`. Explicit-fields signature — no `ToolResult` synthesis. **This is the first home of the helper.** Step 5's `_render_unit_atomic` calls it directly for tool units that have a result; step 6 only consumes the helper (tier dispatch is added in step 6 around the same call). Pulling the extraction into step 5 keeps step 5 self-testable: test #13 (`_render_unit_atomic` body rendering) needs body lines to actually render, which means the helper must already exist.

## HOW

- `append_unit(unit, lines, style=...)`:
  1. Register: `self._units[unit.id] = unit`.
  2. For tools (`kind == "tool"`): write exactly **one** `(unit.id, None)` entry to `_script` (atomic). This is the ONLY script entry for a tool unit — no further `_script` writes ever happen for it. `_render_unit_atomic` reconstructs the full tool block (start lines always; body lines when `unit.output_lines` is non-empty — the pre-rendered triple is the trigger, not the full `output` string) at render time.
  3. For `user_input`: write one `(unit.id, None)` entry to `_script` (also atomic). Call `_write_unit_atomic(unit, lines, style)` which writes all lines and pushes `(start, end, unit.id)` to `_ranges` and to `_screen_lines`.
  4. For `assistant_turn`: register the unit but DO NOT append a script entry. Lines arrive via `extend_open_unit`.
- `extend_open_unit(unit_id, lines, style=...)`:
  1. **Raise `ValueError`** if `self._units[unit_id].kind == "tool"`. Tools never extend; mutations land via `update_unit_and_rerender`.
  2. For each line: append `(unit_id, line)` to `_script`, write the line, append `(start, end, unit_id)` to `_ranges`, append to `_screen_lines`.
- `finalize_open_unit(unit_id)`: no-op in this step. (Marker for clarity / future state; the unit's "openness" is implicit — anyone can still call `extend_open_unit` on a registered turn unit_id.)
- `update_unit_and_rerender(unit_id, **fields)`:
  1. `new_unit = dataclasses.replace(self._units[unit_id], **fields)`.
  2. `self._units[unit_id] = new_unit`.
  3. Call `self.rebuild()` so the new fields take effect (notably tool body / `is_error` / `duration_ms` for atomic tool units).
  4. Return `new_unit`.
- `rebuild()`: minimal implementation in this step. Walks `_script` and re-renders. For atomic entries (`(unit_id, None)`) calls `_render_unit_atomic(unit)`; for streamed entries (`(unit_id, line)`) writes the literal line. **Step 5's `_render_unit_atomic` is the non-tier version**: for tools it always uses the compressed (tier-2) shape; for `user_input` / `assistant_turn` it uses the kind-specific renderer. Step 6 changes `_render_unit_atomic` to dispatch on tier (oneline vs compressed), but the rebuild walk itself does not change.
- `unit_at_line(line)`: linear scan `_ranges`, return `self._units[uid]` for the **first** `(start, end, uid)` with `start <= line < end`. Disjoint ranges by construction → first match wins.
- `last_unit()`: returns last value in `self._units` (insertion order) or `None` if empty.
- `rendered_lines`: returns `list(self._screen_lines)`.
- `clear_state()`: clears all of `_recorded`, `_units`, `_script`, `_ranges`, `_screen_lines`, `_tool_tier_overrides`. Note: `clear()` (RichLog's own buffer wipe) is separate and is called first by the app; `clear_state()` then wipes the model.

**Rename ownership:** Step 5 owns the `clear_recorded() → clear_state()` rename, including updating **both** call sites in `app.py`: `on_input_area_input_submitted` (after `/clear`) and `do_resume`. Step 1's UI dispatch case for `ClearOutput` calls `output.clear_state()` (after step 5 ships). Step 9 does NOT touch this rename — the symbol is already `clear_state` by the time step 9 lands.

Wrap-aware sizing: measure `len(self.lines)` (the RichLog buffer) BEFORE and AFTER each `super().write(...)` to capture the actual rendered span (one logical line may wrap to N buffer lines). The `(start, end)` stored is over `self.lines`, NOT over `_screen_lines`. Also append the logical line to `_screen_lines`. `unit_at_line(line)` interprets `line` against `self.lines` indices (the buffer the click handler will use).

`append_text()` is **untouched** — keeps current implementation (writes to `_recorded` and `super().write()`), does not touch any of the new state.

## ALGORITHM (append_unit atomic write)

```
buffer_start = len(self.lines)
for ln in lines:
    self._recorded.append(ln)                      # existing behavior preserved
    self._screen_lines.append(ln)
    if style: super().write(Text(ln, style=style))
    else:     super().write(ln)
buffer_end = len(self.lines)
self._units[unit.id] = unit
self._script.append((unit.id, None))
self._ranges.append((buffer_start, buffer_end, unit.id))
```

For `extend_open_unit`, same pattern but one range entry per line.

## ALGORITHM (rebuild — minimal, non-tier)

```python
def rebuild(self) -> None:
    super().clear()
    self._screen_lines = []
    self._ranges = []
    for unit_id, line in self._script:
        if line is None:
            # atomic entry — render the unit
            unit = self._units[unit_id]
            start_idx = len(self.lines)
            rendered = self._render_unit_atomic(unit)
            for rln in rendered:
                super().write(rln)
                self._screen_lines.append(rln)
            end_idx = len(self.lines) - 1
            if end_idx >= start_idx:
                self._ranges.append((start_idx, end_idx, unit_id))
        else:
            # streamed entry — render the line literally
            start_idx = len(self.lines)
            super().write(line)
            self._screen_lines.append(line)
            end_idx = len(self.lines) - 1
            if end_idx >= start_idx:
                self._ranges.append((start_idx, end_idx, unit_id))
```

`_render_unit_atomic(unit)` in step 5 (non-tier):
- `unit.kind == "tool"`: always use the compressed (tier-2) shape. For the start lines, synthesize a throwaway `ToolStart` and call `format_tool_start(ToolStart(display_name=unit.tool_name, raw_name="", args=unit.args or {}))` — `format_tool_start` only reads `display_name` and `args`, so the empty `raw_name` is harmless and synthesizing a throwaway action is the simplest path (the function keeps its pre-existing `(action: ToolStart, full: bool = False)` signature; see Decisions R6-01). Then, **if and only if `unit.output_lines` is non-empty**, append the body via `format_tool_compressed(name=unit.tool_name, args=unit.args or {}, output_lines=unit.output_lines, total_lines=unit.total_lines, truncated=unit.truncated, duration_ms=unit.duration_ms, is_error=unit.is_error)`. The `format_tool_compressed` helper itself is introduced in this step (see WHAT — Extracted helper). If `unit.output_lines` is empty (in-flight tool, no result yet), only the start lines are returned — no `└ done` footer. `ToolStart` lives in `src/mcp_coder/llm/types.py` — `output_log.py` imports it for the synthesis.
- `unit.kind == "user_input"`: `[f"> {unit.full_text}"]`.
- `unit.kind == "assistant_turn"`: never reached via atomic entry — turns arrive as `(unit_id, line)` script entries.

Step 6 extends `_render_unit_atomic` to dispatch on effective tier (`_tool_tier_overrides.get(unit_id, _tool_display_default)`), returning `format_tool_oneline(...)` for tier 1 or the existing compressed body for tier 2. The rebuild walk above does not change in step 6.

## DATA

- `ContentUnit` is frozen — fields set at creation, never mutated.
- `_ranges` indices are over `RichLog.lines` (buffer-line space), not logical lines.
- `_screen_lines` is logical lines (one entry per call, no wrap expansion).

## TDD

Tests in `tests/icoder/ui/test_output_log.py` (use existing pilot/textual pattern), plus three new `format_tool_compressed` tests in `tests/llm/formatting/test_stream_renderer.py` (migrated from step 6 alongside the helper extraction):

1. `test_append_unit_registers_unit_and_range` — append a tool unit with 3 lines → `_units` has entry; `_ranges` has one tuple covering 3 lines; `unit_at_line(0)` returns it.
2. `test_unit_at_line_returns_none_outside_range`
3. `test_unit_at_line_disjoint_ranges` — append two units → each line resolves to the correct unit; gaps return `None`.
4. `test_extend_open_unit_adds_range_per_line` — begin turn, extend with 3 lines → 3 range entries, all map to the same unit_id; `unit_at_line` resolves any of them to the same unit.
5. `test_extend_open_unit_interleaves_with_tool` — turn + extend 2 lines + tool unit + extend 2 lines → 5 range entries (2 turn + 1 tool + 2 turn), first-match resolves tool lines to tool unit, turn lines to turn unit.
6. `test_last_unit_returns_most_recent` — append A then B → `last_unit().id == "B"`.
7. `test_last_unit_none_when_empty`
8. `test_rendered_lines_reflects_screen_state` — after multiple appends, `rendered_lines` matches the logical lines written.
9. `test_recorded_lines_independent_of_units` — append units → both `_recorded` and `_screen_lines` grow; calling `append_text` writes only to `_recorded` and screen (no unit / range).
10. `test_clear_state_wipes_all_state` — populate units + ranges; call `clear_state()` → `_units`, `_script`, `_ranges`, `_screen_lines`, `_recorded`, `_tool_tier_overrides` all empty.
11. `test_wrapped_line_range_uses_buffer_index` — write a very long line that wraps to N buffer lines → range `end - start == N`.
12. `test_extend_open_unit_raises_for_tool_kind` — append a tool unit; call `extend_open_unit(tool_id, ["x"])` → `ValueError`.
13. `test_update_unit_and_rerender_replaces_and_rebuilds` — append a tool unit with `output=None`; call `update_unit_and_rerender(uid, output="X", output_lines=("X",), total_lines=1, truncated=False, duration_ms=42, is_error=False)` → `_units[uid].output == "X"`, `rendered_lines` includes the body.
14. `test_content_unit_parent_id_defaults_none` — `ContentUnit(...)` without `parent_id` argument has `parent_id is None` (v1 invariant).
15. `test_append_unit_assistant_turn_with_empty_lines_no_script_entry` — calling `append_unit(unit, [])` with `unit.kind == "assistant_turn"` registers the unit in `_units` but does NOT add a `(unit_id, None)` entry to `_script`. The turn waits for `extend_open_unit` calls before any script entries land; before then, `rebuild()` walks past the turn (no atomic write). Also assert: `rebuild()` produces zero buffer lines for that empty turn — no `(unit_id, None)` entry in `_script` means the rebuild walk skips it entirely.

Tests in `tests/llm/formatting/test_stream_renderer.py` (cover the newly extracted helper):

16. `test_format_tool_compressed_done` — pass `output_lines=("a","b")`, `total_lines=2`, `duration_ms=120`, `is_error=False` → body lines start with `│  ` and footer is `└ done (2 lines, 120ms)`.
17. `test_format_tool_compressed_error` — `is_error=True` → footer is `└ error`.
18. `test_format_tool_compressed_empty_output` — `output_lines=()`, `total_lines=0` → only footer line returned.

### Existing test audit (mandatory sub-step)

Walk `tests/icoder/ui/test_output_log.py` (2 existing tests today) and any other test asserting on `OutputLog.recorded_lines`. Classify each:

- **Emission semantics** ("was this text appended?") → keep using `recorded_lines`.
- **Screen-state semantics** ("what is currently visible after a clear and re-render?") → migrate to `rendered_lines` (later, once step 6 lands). In step 5, just document the migration target — no behavior change yet.

Add a docstring comment in `output_log.py` codifying:
- `recorded_lines`: append history; survives toggles/rebuilds.
- `rendered_lines`: current screen state; reflects toggles/rebuilds.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 5** from `pr_info/steps/step_5.md` (OutputLog registry data layer).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - **No tier model, no toggle** in this step — those are step 6. Step 5 implements a minimal `rebuild()` (see ALGORITHM section) that walks `_script` and re-renders via the non-tier `_render_unit_atomic` (tools always render compressed). Step 6 then changes `_render_unit_atomic` to dispatch on effective tier; the rebuild walk itself does not change.
> - `append_text()` semantics unchanged.
> - `ContentUnit` is `frozen=True`; per-unit tier overrides live on `OutputLog`, not on `ContentUnit` (step 6).
> - `ContentUnit.parent_id: str | None = None` — always `None` in v1, reserved for v2 nesting per issue #629 Decision.
> - Tools are atomic: `append_unit` writes one `(unit.id, None)` script entry; `extend_open_unit` **raises** for tool kind; mutations go through `update_unit_and_rerender`.
> - `_ranges` indices are over the RichLog buffer (`self.lines`), wrap-aware (measure before/after write).
> - First-match wins on `unit_at_line` (ranges are disjoint by construction).
> - `clear_state()` (renamed from `clear_recorded()`) wipes the full model including `_tool_tier_overrides`. Update call sites in `app.py`.
> - Audit existing tests using `recorded_lines`; document classification (emission vs. screen).
> - Add code comment near `__init__` noting `max_lines` must stay `None`.
> - Extract `format_tool_compressed(name, args, output_lines, total_lines, truncated, duration_ms, is_error) -> list[str]` into `src/mcp_coder/llm/formatting/stream_renderer.py` alongside `format_tool_start` / `format_tool_oneline`. Explicit-fields signature — no `ToolResult` synthesis. Step 5's `_render_unit_atomic` calls it directly; step 6 only adds tier dispatch around the call.
> - Declare `_tool_tier_overrides: dict[str, Literal["oneline", "compressed"]] = field(default_factory=dict)` on `OutputLog`. Field is empty in step 5; step 6 introduces both the populating methods (`toggle_unit_tier`, `set_tool_display_default`) and the `_tool_display_default` companion field. `clear_state()` must wipe `_tool_tier_overrides`.
> - TDD: write the 18 new test cases first (15 in `tests/icoder/ui/test_output_log.py` + 3 in `tests/llm/formatting/test_stream_renderer.py`), then implement.
>
> All three quality gates green after the change.
