# Step 6 — `OutputLog` tier model + `toggle_unit_tier` + tier dispatch + `on_resize`

## Goal

Layer the tier model on top of the registry from step 5:
- Track a global default tier (`compressed` initially) and per-unit overrides.
- Expose `toggle_unit_tier(unit_id)`.
- Extend `_render_unit_atomic` to dispatch on effective tier (oneline vs compressed). The `rebuild()` walk itself does not change — it's already implemented in step 5, and `format_tool_compressed` was extracted in step 5.
- Wire `on_resize` to call `rebuild()` (wrap-derived ranges invalidate on resize).
- `set_tool_display_default(tier)` updates the default AND wipes per-unit overrides (the `/display` hard reset).

Click handlers and the App layer wire-up come in steps 8 and 9.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/output_log.py` — tier state (`_tool_display_default` added here; `_tool_tier_overrides` is already declared in step 5) + tier methods + tier dispatch inside `_render_unit_atomic` + `on_resize`
- `tests/icoder/ui/test_output_log.py` — tier and rebuild tests

## WHAT

```python
class OutputLog(RichLog):
    # `_tool_tier_overrides` is already declared in step 5 (empty by default).
    # Step 6 adds the companion default plus the populating methods.
    _tool_display_default: Literal["oneline", "compressed"] = "compressed"

    def effective_tier(self, unit_id: str) -> Literal["oneline", "compressed"]
    def toggle_unit_tier(self, unit_id: str) -> Literal["oneline", "compressed"]
    def set_tool_display_default(self, tier: Literal["oneline", "compressed"]) -> None
    def on_resize(self, event: object) -> None        # textual hook
```

Internal helpers (the method body is extended here; the method itself exists from step 5):

```python
def _render_unit_atomic(self, unit: ContentUnit) -> tuple[list[str], str | None]
    # tool → tier-aware rendering (oneline OR compressed); returns (lines, style)
    # user_input → ([f"> {unit.full_text}"], STYLE_USER_INPUT)
```

`format_tool_compressed(...)` already exists in `src/mcp_coder/llm/formatting/stream_renderer.py` — it was extracted in step 5 alongside the helper's first call site inside `_render_unit_atomic`. Step 6 only adds tier dispatch around the existing call. Step 9's `_handle_stream_event` ToolResult branch (live streaming) reaches the same helper **indirectly** via `update_unit_and_rerender → rebuild → _render_unit_atomic` — step 9 itself does NOT call `format_tool_compressed`. Byte-identical output is guaranteed because the initial render and any subsequent rebuilds go through the same code path.

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
  3. Call `self.rebuild()` (`rebuild` exists from step 5).
- `rebuild()`: **no changes in this step** — already implemented in step 5. The rebuild walk picks up the new tier dispatch automatically because `_render_unit_atomic` (called from rebuild) now reads `_tool_tier_overrides` / `_tool_display_default`.
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

`rebuild()` is unchanged from step 5 — its walk over `_script` already routes atomic entries through `_render_unit_atomic`, so the new tier dispatch added in this step takes effect automatically on the next rebuild. No re-implementation needed here.

## DATA

- `_tool_display_default` default at `__init__`: `"compressed"`.
- `_tool_tier_overrides` only gets entries on explicit toggle.
- `toggle_unit_tier` returns the new tier string.

## TDD

Tests in `tests/icoder/ui/test_output_log.py` (all 11 cover tier dispatch + override-aware render path; the `format_tool_compressed` unit tests were migrated to step 5 along with the helper extraction):

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

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 6** from `pr_info/steps/step_6.md` (tier model + rebuild + on_resize).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Tier overrides live on `OutputLog`, NOT on `ContentUnit` (which stays `frozen=True`). `_tool_tier_overrides` is already declared in step 5; this step adds `_tool_display_default` and the populating methods.
> - `set_tool_display_default()` is the `/display` hard reset — updates default AND wipes overrides.
> - `rebuild()` is unchanged in this step — it ships in step 5 and the new tier dispatch inside `_render_unit_atomic` takes effect on the next rebuild automatically.
> - `format_tool_compressed(...)` already exists in `stream_renderer.py` (extracted in step 5). Step 6 only adds tier dispatch around its existing call site inside `_render_unit_atomic`.
> - `_recorded` is never touched by `rebuild()`.
> - `_render_unit_atomic` for tool kind: start lines always; body lines only when `unit.output_lines` is non-empty.
> - TDD: 11 test cases (all in `tests/icoder/ui/test_output_log.py`) first, then implement.
>
> All three quality gates green after the change.
