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

### Changes to snapshot tests

- Snapshot test fixtures must inject a fixed version string (e.g., `"0.0.0-test"` via `RuntimeInfo` or by mocking `importlib.metadata.version`) to prevent breakage on version bumps.
- Add Textual async tests for `_update_token_display()` verifying widget text and hidden-class behavior (see DATA section for details).

## HOW

- Snapshot tests must use a fixed version string (see DATA section) to avoid fragile snapshots
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
    widget.remove_class("hidden")
else:
    widget.add_class("hidden")
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

**Version stability**: Snapshot test fixtures must pass a `RuntimeInfo` with a fixed version to `AppCore` so the status bar renders a stable version string. Update the `icoder_app` fixture:

```python
from mcp_coder.icoder.runtime_info import RuntimeInfo

@pytest.fixture
def icoder_app(...):
    runtime_info = RuntimeInfo(mcp_coder_version="0.0.0-test")
    app_core = AppCore(..., runtime_info=runtime_info)
    ...
```

This prevents snapshot breakage whenever mcp-coder is released with a new version number.

### Tests for `_update_token_display()` (in `test_snapshots.py` or a new `test_status_bar.py`)

Add Textual async tests that verify the status bar update logic beyond snapshots:

1. **`test_token_display_updates_after_stream_with_usage`** -- Run a stream with usage data (`{"type": "done", "usage": {"input_tokens": 1200, "output_tokens": 800}}`), then assert that `#status-tokens` text contains the formatted counts (e.g., `"\u21931.2k \u2191800"`) and does NOT have the `hidden` class.
2. **`test_token_display_hidden_after_stream_without_usage`** -- Run a stream with `{"type": "done"}` (no usage key), then assert that `#status-tokens` has the `hidden` class.

Use existing test patterns from `tests/icoder/test_app_core.py` and `tests/icoder/test_snapshots.py` for fixture setup (FakeLLMService, patched store_session, etc.).
