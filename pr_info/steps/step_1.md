# Step 1: Create `BusyIndicator` Widget with Tests

> See [summary.md](summary.md) for full context and architectural decisions.

## LLM Prompt

Implement the `BusyIndicator` widget for iCoder (issue #752). Read `pr_info/steps/summary.md` for context, then implement this step. Create the widget and its tests. Add CSS styling. Do NOT modify `app.py` yet — that is step 2.

## WHERE

- **Create**: `src/mcp_coder/icoder/ui/widgets/busy_indicator.py`
- **Create**: `tests/icoder/test_busy_indicator.py`
- **Modify**: `src/mcp_coder/icoder/ui/styles.py` — add CSS for `BusyIndicator`

## WHAT

### `BusyIndicator(Static)` — widget class

```python
class BusyIndicator(Static):
    def on_mount(self) -> None: ...
    def show_busy(self, message: str) -> None: ...
    def show_ready(self) -> None: ...
    def _on_tick(self) -> None: ...
```

### Public methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `show_busy` | `(self, message: str) -> None` | Set busy state, record start time, update label |
| `show_ready` | `(self) -> None` | Reset to idle `✓ Ready` |

### Internal state

| Field | Type | Purpose |
|-------|------|---------|
| `_busy` | `bool` | Whether spinner is active |
| `_message` | `str` | Current status text |
| `_start_time` | `float` | `monotonic()` when `show_busy` was last called |
| `_frame` | `int` | Current spinner frame index |

## HOW

- Subclass `textual.widgets.Static`
- `on_mount`: call `self.set_interval(0.15, self._on_tick)` and `self.update("✓ Ready")`
- CSS in `styles.py`: `BusyIndicator { height: 1; background: #1e1e1e; color: #666666; }`

## ALGORITHM

```
on_mount:
    set_interval(0.15, _on_tick)
    update("✓ Ready")

show_busy(message):
    if not _busy: _start_time = monotonic()
    _busy = True, _message = message
    _update_label()

show_ready:
    _busy = False
    update("✓ Ready")

_on_tick:
    if not _busy: return
    _frame = (_frame + 1) % len(FRAMES)
    _update_label()

_update_label:
    elapsed = monotonic() - _start_time
    update(f"{FRAMES[_frame]} {_message} [{elapsed:.1f}s]")
```

## DATA

- `SPINNER_FRAMES`: `tuple[str, ...]` = `("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")`
- Ready state renders: `"✓ Ready"`
- Busy state renders: `"⠋ Thinking... [1.2s]"` or `"⠋ workspace > read_file [3.2s]"`

## TESTS (`tests/icoder/test_busy_indicator.py`)

Tests use a minimal `App` that hosts just `BusyIndicator` (same pattern as `WidgetTestApp` in `test_widgets.py`).

Tests need `pytestmark = pytest.mark.textual_integration` at module level, consistent with existing test patterns in `test_app_pilot.py`.

1. **`test_initial_state_shows_ready`** — After mount, widget renders `✓ Ready`
2. **`test_show_busy_updates_label`** — `show_busy("Thinking...")` renders spinner + message + elapsed
3. **`test_show_ready_resets`** — After `show_busy` then `show_ready`, widget shows `✓ Ready` again
4. **`test_show_busy_preserves_start_time`** — After `show_busy("A")`, wait briefly, then `show_busy("B")` — rendered elapsed time is still > 0 (timer was not reset)
5. **`test_show_busy_after_ready_resets_start_time`** — After `show_busy` → `show_ready` → `show_busy` — rendered elapsed time starts from ~0 (timer was reset)
6. **`test_spinner_frame_advances`** — After a tick, the rendered spinner character has changed from its initial value

## Commit

```
feat(icoder): add BusyIndicator widget with spinner animation (#752)
```
