# Issue #683 — iCoder Improve Layout

## Summary

Five targeted changes to the iCoder TUI to fix usability issues in VS Code's integrated terminal:
1. Enable line wrapping in the output log (no more horizontal scrolling)
2. Set explicit foreground/background colors so text is visible in all terminals
3. Make the input box grow with content instead of staying at 1 line
4. Regenerate snapshot test baselines after the visual changes
5. Add documentation comments explaining the snapshot testing workflow

## Architectural / Design Changes

**No structural or architectural changes.** All modifications are within the existing `icoder.ui` module:

- **OutputLog widget** — constructor gains `wrap=True` (behavioral config, no API change)
- **CSS styles** — explicit colors added, `max-height` removed (CSS-only)
- **InputArea widget** — new `on_text_area_changed` handler for dynamic height sizing. This is the only new logic: it reads `document.line_count` and `screen.size.height` to set `styles.height`. The approach uses Textual's built-in message system rather than introducing reactive properties.
- **Snapshot baselines** — regenerated SVGs (binary artifacts, not code)
- **Documentation** — comments only, no code changes

Existing Rich styles in `app.py` (`STYLE_USER_INPUT`, `STYLE_TOOL_OUTPUT`) are untouched — they override the new CSS defaults locally where applied.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/widgets/output_log.py` | Add `wrap=True` to constructor |
| `src/mcp_coder/icoder/ui/styles.py` | Add colors to both widgets, remove `max-height: 5` from InputArea |
| `src/mcp_coder/icoder/ui/widgets/input_area.py` | Add `on_text_area_changed` height handler |
| `tests/icoder/__snapshots__/test_snapshots/*.svg` | Regenerated baselines (3 files) |
| `tests/icoder/test_snapshots.py` | Add documentation comments |
| `pyproject.toml` | Add comment near `textual_integration` marker |

## Files Created

None.

## Implementation Steps

1. **OutputLog wrap + colors** — `wrap=True` in OutputLog, explicit colors for both widgets in CSS
2. **InputArea auto-grow** — remove `max-height`, add reactive height handler
3. **Snapshot regeneration + documentation** — update baselines, add comments
