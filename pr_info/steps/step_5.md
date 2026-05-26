# Step 5 — `OutputLog` registry data layer

## Goal

Add the sidecar `(start, end) → unit_id` registry and the `append_unit` / `extend_open_unit` / `finalize_open_unit` / `unit_at_line` / `last_unit` / `rendered_lines` API. **No tier model yet, no toggle, no rebuild** — those land in step 6.

Existing `append_text()` semantics unchanged. Banners, spacers, "Resumed" divider, cancelled marker all keep using `append_text()`.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/output_log.py` — `ContentUnit` dataclass + new state + methods
- `tests/icoder/ui/test_output_log.py` — new tests; **audit existing tests** asserting on `recorded_lines`

## WHAT

```python
@dataclass(frozen=True)
class ContentUnit:
    id: str
    kind: Literal["tool", "user_input", "assistant_turn"]
    timestamp: datetime
    full_text: str = ""
    # tool-only (None for non-tool kinds):
    tool_name: str | None = None
    args: dict[str, object] | None = None
    output: str | None = None
    duration_ms: int | None = None
    is_error: bool = False

class OutputLog(RichLog):
    # existing _recorded stays as APPEND HISTORY (never rebuilt)
    _units: dict[str, ContentUnit]                    # insertion-ordered
    _script: list[tuple[str, str | None]]             # (unit_id, line | None)
    _ranges: list[tuple[int, int, str]]               # (start, end, unit_id)
    _screen_lines: list[str]                          # current screen state

    def append_unit(self, unit: ContentUnit, lines: list[str], style: str | None = None) -> None
    def extend_open_unit(self, unit_id: str, lines: list[str], style: str | None = None) -> None
    def finalize_open_unit(self, unit_id: str) -> None      # no-op marker (see HOW)
    def unit_at_line(self, line: int) -> ContentUnit | None
    def last_unit(self) -> ContentUnit | None
    @property
    def rendered_lines(self) -> list[str]
    def clear_recorded(self) -> None                  # EXTENDED: also wipes _units/_script/_ranges/_screen_lines
```

Add a one-line code comment at `__init__` noting `max_lines` must remain `None` (eviction would invalidate `_ranges`).

## HOW

- `append_unit(unit, lines, style=...)`:
  1. Register: `self._units[unit.id] = unit`.
  2. For each rendered line, append to `_script` as `(unit.id, None)` if kind is `tool` or `user_input` (atomic — write the line and register one range entry per logical block). Implementation choice: **one script entry per logical unit for atomic units**. We use `(unit.id, None)` as a marker meaning "render this unit's full content from raw data". Then on first write we call `_write_unit_atomic(unit, lines, style)` which writes all lines and pushes `(start, end, unit.id)` to `_ranges` and to `_screen_lines`.
  3. For `assistant_turn`: register the unit but DO NOT append a script entry. Lines arrive via `extend_open_unit`.
- `extend_open_unit(unit_id, lines, style=...)`:
  1. For each line: append `(unit_id, line)` to `_script`, write the line, append `(start, end, unit_id)` to `_ranges`, append to `_screen_lines`.
- `finalize_open_unit(unit_id)`: no-op in this step. (Marker for clarity / future state; the unit's "openness" is implicit — anyone can still call `extend_open_unit` on a registered unit_id.)
- `unit_at_line(line)`: linear scan `_ranges`, return `self._units[uid]` for the **first** `(start, end, uid)` with `start <= line < end`. Disjoint ranges by construction → first match wins.
- `last_unit()`: returns last value in `self._units` (insertion order) or `None` if empty.
- `rendered_lines`: returns `list(self._screen_lines)`.
- `clear_recorded()`: clears all of `_recorded`, `_units`, `_script`, `_ranges`, `_screen_lines`.

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

## DATA

- `ContentUnit` is frozen — fields set at creation, never mutated.
- `_ranges` indices are over `RichLog.lines` (buffer-line space), not logical lines.
- `_screen_lines` is logical lines (one entry per call, no wrap expansion).

## TDD

Tests in `tests/icoder/ui/test_output_log.py` (use existing pilot/textual pattern):

1. `test_append_unit_registers_unit_and_range` — append a tool unit with 3 lines → `_units` has entry; `_ranges` has one tuple covering 3 lines; `unit_at_line(0)` returns it.
2. `test_unit_at_line_returns_none_outside_range`
3. `test_unit_at_line_disjoint_ranges` — append two units → each line resolves to the correct unit; gaps return `None`.
4. `test_extend_open_unit_adds_range_per_line` — begin turn, extend with 3 lines → 3 range entries, all map to the same unit_id; `unit_at_line` resolves any of them to the same unit.
5. `test_extend_open_unit_interleaves_with_tool` — turn + extend 2 lines + tool unit + extend 2 lines → 5 range entries (2 turn + 1 tool + 2 turn), first-match resolves tool lines to tool unit, turn lines to turn unit.
6. `test_last_unit_returns_most_recent` — append A then B → `last_unit().id == "B"`.
7. `test_last_unit_none_when_empty`
8. `test_rendered_lines_reflects_screen_state` — after multiple appends, `rendered_lines` matches the logical lines written.
9. `test_recorded_lines_independent_of_units` — append units → both `_recorded` and `_screen_lines` grow; calling `append_text` writes only to `_recorded` and screen (no unit / range).
10. `test_clear_recorded_wipes_all_state` — populate units + ranges; call `clear_recorded()` → `_units`, `_script`, `_ranges`, `_screen_lines`, `_recorded` all empty.
11. `test_wrapped_line_range_uses_buffer_index` — write a very long line that wraps to N buffer lines → range `end - start == N`.

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
> - **No tier model, no toggle, no rebuild** in this step — those are step 6.
> - `append_text()` semantics unchanged.
> - `ContentUnit` is `frozen=True`; per-unit tier overrides live on `OutputLog`, not on `ContentUnit` (step 6).
> - `_ranges` indices are over the RichLog buffer (`self.lines`), wrap-aware (measure before/after write).
> - First-match wins on `unit_at_line` (ranges are disjoint by construction).
> - Audit existing tests using `recorded_lines`; document classification (emission vs. screen).
> - Add code comment near `__init__` noting `max_lines` must stay `None`.
> - TDD: write the 11 new test cases first, then implement.
>
> All three quality gates green after the change.
