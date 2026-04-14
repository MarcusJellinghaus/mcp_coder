# Step 3: Three-Zone Status Bar UI + CSS

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #808).

## Goal

Replace the `#input-hint` Static widget with a three-zone status bar (`Horizontal` container with three `Static` children). Remove the hide-on-typing behavior. Update the `StreamDone` handler to pull token usage from `app_core.token_usage`. Update CSS. Regenerate snapshot baselines.

## LLM Prompt

```
Implement Step 3 of Issue #808 (see pr_info/steps/summary.md for context).

Replace #input-hint with a 3-zone status bar in icoder/ui/app.py:
- #status-tokens (left): token counts, or hidden when no data
- #status-version (center): mcp-coder version
- #status-hint (right): "\ + Enter = newline"

Remove on_text_area_changed(). Update _handle_stream_event StreamDone
branch to pull token_usage. Update CSS in styles.py.
Regenerate snapshot SVGs with --snapshot-update.
Run all three code quality checks after changes.
```

## WHERE

- **Modify**: `src/mcp_coder/icoder/ui/app.py`
- **Modify**: `src/mcp_coder/icoder/ui/styles.py`
- **Modify**: `tests/icoder/test_snapshots.py` (regenerate baselines)
- **Modify**: `tests/icoder/__snapshots__/*.svg` (regenerated)

## WHAT

### Changes to `app.py`

#### New import
```python
from textual.containers import Horizontal
import importlib.metadata
```

#### Replace in `compose()`
**Remove**:
```python
yield Static(r"\ + Enter = newline", id="input-hint")
```

**Add**:
```python
version = self._get_version()
with Horizontal(id="status-bar"):
    yield Static("↓0 ↑0 | total: ↓0 ↑0", id="status-tokens")
    yield Static(f"v{version}", id="status-version")
    yield Static(r"\ + Enter = newline", id="status-hint")
```

#### New method `_get_version()`
```python
def _get_version(self) -> str:
    if self._core.runtime_info:
        return self._core.runtime_info.mcp_coder_version
    try:
        return importlib.metadata.version("mcp-coder")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"
```

#### Delete `on_text_area_changed()` entirely

#### Update `_handle_stream_event()` — `StreamDone` branch
```python
if isinstance(action, StreamDone):
    self.query_one(BusyIndicator).show_ready()
    self._update_token_display()
    self._append_blank_line()
```

#### New method `_update_token_display()`
```python
def _update_token_display(self) -> None:
    """Update status bar token zone from app_core.token_usage."""
    usage = self._core.token_usage
    token_widget = self.query_one("#status-tokens", Static)
    if usage.has_data:
        token_widget.update(usage.display_text())
        token_widget.remove_class("hidden")
    else:
        token_widget.add_class("hidden")
```

### Changes to `styles.py`

**Remove**:
```css
#input-hint {
    height: 1;
    background: #1e1e1e;
    color: #666666;
    text-align: right;
}

#input-hint.hidden {
    display: none;
}
```

**Add**:
```css
#status-bar {
    height: 1;
    background: #1e1e1e;
    color: #666666;
}

#status-tokens {
    width: 1fr;
}

#status-version {
    width: auto;
}

#status-hint {
    width: 1fr;
    text-align: right;
}

#status-tokens.hidden {
    display: none;
}
```

## HOW

- `Horizontal` container with `id="status-bar"` gives the three-zone layout
- `width: 1fr` on left and right zones makes them share remaining space equally
- `width: auto` on center version zone sizes to content
- The `.hidden` class on `#status-tokens` uses `display: none` to hide when provider gives no data
- `_update_token_display()` called from `_handle_stream_event` on `StreamDone` — pull model

## ALGORITHM

### `_update_token_display()`
```
usage = self._core.token_usage
widget = query("#status-tokens")
if usage.has_data:
    widget.update(usage.display_text())
    widget.show()
else:
    widget.hide()
```

### Initial state in `compose()`
```
# Before any LLM call: show zeroes (decision #6)
# The "↓0 ↑0 | total: ↓0 ↑0" text is set as initial content
# After first StreamDone without usage data: hidden via _update_token_display
```

## DATA

### Status bar states

| State | #status-tokens | #status-version | #status-hint |
|-------|---------------|----------------|-------------|
| Initial (no LLM call) | `↓0 ↑0 \| total: ↓0 ↑0` | `v0.8.0` | `\ + Enter = newline` |
| After stream (with usage) | `↓1.2k ↑800 \| total: ↓1.2k ↑800` | `v0.8.0` | `\ + Enter = newline` |
| After stream (no usage) | *hidden* | `v0.8.0` | `\ + Enter = newline` |

### Snapshot regeneration

Run: `pytest tests/icoder/test_snapshots.py --snapshot-update`

All existing snapshots will change because:
1. `#input-hint` replaced by `#status-bar` with different layout
2. Content changes (version string, token counts visible)
