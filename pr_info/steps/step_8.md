# Step 8 — Click handler on `OutputLog` + `F2` binding on `ICoderApp`

## Goal

Wire user interactions:
- Left single click on a tool unit → debounced (~250 ms) `toggle_unit_tier`.
- Left double click on any unit → open `DetailModal`.
- `chain >= 3` → ignored.
- Right / middle button → ignored.
- Click on a banner / blank / non-unit line → no-op (`unit_at_line` returns `None`).
- `F2` on `ICoderApp` → open modal for `output.last_unit()` (silent no-op if `None`).

App-layer integration of `append_unit` (so units actually exist for clicks) lands in step 9.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/output_log.py` — `on_click` handler + pending-single timer state
- `src/mcp_coder/icoder/ui/app.py` — add `F2` binding + `action_open_last_unit_modal`
- `tests/icoder/test_app_pilot.py` — click / chain / right-button / F2 behaviors via Pilot
- `tests/icoder/ui/test_output_log.py` — debounce / chain semantics

## WHAT

```python
# OutputLog additions
_pending_single: Timer | None = None
_on_unit_event: Callable[[str, dict[str, object]], None] | None = None   # injected via __init__

def on_click(self, event: Click) -> None: ...

# ICoderApp additions
BINDINGS = [
    ..., Binding("f2", "open_last_unit_modal", "Detail", show=False),
]
def action_open_last_unit_modal(self) -> None: ...
```

## HOW

Before writing the click tests, run a 5-line spike: verify that `event.y + self.scroll_offset.y` resolves to the correct index in `self.lines` for the current Textual version. If `event.style.meta` is populated with the unit_id from `Strip` metadata, prefer that path (no coordinate math).

- `on_click`:
  1. If `event.button != 1`: return (left only).
  2. If `event.chain >= 3`: return.
  3. Resolve clicked logical line: `clicked_line = self.scroll_offset.y + event.y` (verify against current Textual API; alt: `event.style.meta` if Textual exposes it for RichLog).
  4. `unit = self.unit_at_line(clicked_line)`; if `None`: return.
  5. If `event.chain == 2`:
     - Cancel any `_pending_single` timer.
     - `self.app.push_screen(DetailModal(unit))`.
     - Emit `content_detail_opened` via the `on_unit_event` callback (if wired).
     - Return.
  6. `event.chain == 1`: schedule `set_timer(0.25, lambda: self._handle_single(unit))` and store in `_pending_single`.
- `_handle_single(unit)`:
  1. If `unit.kind != "tool"`: return (only tools toggle).
  2. `new_tier = self.toggle_unit_tier(unit.id)`.
  3. Emit `tool_tier_toggled` via the `on_unit_event` callback (if wired) with payload `{"unit_id": unit.id, "new_tier": new_tier}`.
- `action_open_last_unit_modal()` (on ICoderApp):
  1. `output = self.query_one(OutputLog)`.
  2. `unit = output.last_unit()`.
  3. If `None`: return silently.
  4. `self.push_screen(DetailModal(unit))`. Emit `content_detail_opened`.

### Event log wiring

`OutputLog` does NOT own the event log. Add an `on_unit_event: Callable[[str, dict[str, object]], None] | None = None` parameter to `OutputLog.__init__` (mirrors the existing `mirror` callback pattern). `ICoderApp.compose` wires it to `self._core.event_log.append` (or equivalent emit method). All event emissions from within `OutputLog` go through `self._on_unit_event(name, payload)` if set. Do NOT access `self.app._core.event_log` directly from `OutputLog`.

## ALGORITHM (on_click)

```
if event.button != 1: return
if event.chain >= 3: return
line = self.scroll_offset.y + event.y
unit = self.unit_at_line(line)
if unit is None: return
if event.chain == 2:
    if self._pending_single: self._pending_single.cancel(); self._pending_single = None
    self.app.push_screen(DetailModal(unit))
    if self._on_unit_event:
        self._on_unit_event("content_detail_opened", {"unit_id": unit.id, "kind": unit.kind})
    return
# chain == 1
self._pending_single = self.set_timer(0.25, lambda: self._handle_single(unit))
```

## DATA

- `_pending_single`: a Textual `Timer` reference; reset to `None` after firing.
- Events emitted: `tool_tier_toggled` (unit_id, new_tier), `content_detail_opened` (unit_id, kind).

## TDD

Tests in `tests/icoder/ui/test_output_log.py` (mostly unit-level — Pilot for click events):

1. `test_click_chain_3_ignored` — feed a `Click` with `chain=3` → no toggle, no modal.
2. `test_click_right_button_ignored` — `button=3` → no-op.
3. `test_click_on_blank_line_noop` — click outside any range → no-op.
4. `test_double_click_cancels_pending_single` — programmatically post chain-1 then chain-2 quickly → single handler never fires.
5. `test_single_click_on_tool_toggles_after_debounce` — chain-1 on a tool unit; advance time past 250 ms → tier flipped.
6. `test_single_click_on_user_input_noops` — chain-1 on user-input unit; advance time → no tier change (not a tool).

Tests in `tests/icoder/test_app_pilot.py`:

7. `test_f2_with_no_content_is_silent_noop` — fresh app, press F2 → no error, no modal pushed.
8. `test_f2_opens_modal_for_last_unit` — append unit via test helper; press F2 → DetailModal screen present.
9. `test_double_click_emits_content_detail_opened_event` — append unit; pilot double-click → event log contains the event.
10. `test_single_click_emits_tool_tier_toggled_event` — append tool unit; pilot single-click + wait > 250 ms → event log contains `tool_tier_toggled`.

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 8** from `pr_info/steps/step_8.md` (click handler + F2 binding).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Left button only; `chain >= 3` ignored; non-tool units ignore single click; clicks on lines outside any range are silent no-ops.
> - 250 ms debounce timer; cancel on `chain == 2`.
> - F2 on `ICoderApp` opens modal for `last_unit()`; silent no-op when no content.
> - `OutputLog` emits events via the `on_unit_event` callback parameter (`__init__`); `ICoderApp.compose` wires it to `self._core.event_log.append`. NO direct access to `self.app._core.event_log` from `OutputLog`. Mirrors the existing `mirror` callback pattern.
> - Run a 5-line spike against the current Textual version BEFORE writing click tests: confirm `event.y + self.scroll_offset.y` maps to the right index in `self.lines`. Prefer `event.style.meta` if it carries the `unit_id` via `Strip` metadata.
> - TDD: 10 test cases first, then implement.
> - Step 9 will wire actual `append_unit` calls in the App; for testing, append units directly via the widget API.
>
> All three quality gates green after the change.
