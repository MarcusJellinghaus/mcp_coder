# Step 7: Snapshot Tests for Dropdown Visual States

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Add SVG snapshot tests for the three key dropdown visual states. These tests capture visual regressions in the autocomplete UI.

## WHERE

| Action | File |
|--------|------|
| Modify | `tests/icoder/test_snapshots.py` |

## WHAT

Three new snapshot tests added to the existing snapshot test file:

```python
def test_snapshot_autocomplete_all_commands(snap_compare, icoder_app):
    """Snapshot: dropdown visible with all commands (user typed '/')."""
    async def type_slash(pilot):
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
    assert snap_compare(icoder_app, run_before=type_slash)

def test_snapshot_autocomplete_filtered(snap_compare, icoder_app):
    """Snapshot: dropdown filtered to single match (user typed '/he')."""
    async def type_prefix(pilot):
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/he")
        await pilot.pause()
    assert snap_compare(icoder_app, run_before=type_prefix)

def test_snapshot_autocomplete_no_match(snap_compare, icoder_app):
    """Snapshot: dropdown showing '(no matching commands)' (user typed '/xyz')."""
    async def type_bad_prefix(pilot):
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/xyz")
        await pilot.pause()
    assert snap_compare(icoder_app, run_before=type_bad_prefix)
```

## HOW

- Follow the existing pattern in `test_snapshots.py`
- Use the existing `icoder_app` fixture (may need adjustment since InputArea now takes registry/event_log — the fixture creates `ICoderApp(app_core)` which handles this internally)
- Windows-only (`sys.platform == "win32"` skip marker already on the module)
- May need to adjust terminal size if the dropdown doesn't fit — check the existing `snap_compare` configuration

## Notes

- Run with `--snapshot-update` first to generate baselines
- Verify generated SVGs contain no secrets, env vars, or local paths
- The dropdown height may require adjusting the `max-height` CSS or the snapshot app size

## Constraint I6: existing snapshot fixture compatibility

Verify the existing `tests/icoder/test_snapshots.py` `ICoderApp(app_core)` fixture still passes after Step 5's `compose()` change (which adds `CommandAutocomplete` to the layout). The existing snapshots may need to be regenerated because the layout includes a new (hidden) widget.

If the existing snapshots break:
1. Confirm the only visual difference is the (hidden) `CommandAutocomplete` widget — there should be no actual visible diff since it has `display: none`.
2. If there is a visible diff, regenerate the existing baselines with `--snapshot-update` and review the diff carefully.
3. If the fixture itself needs adjustment (e.g. terminal size), include that change in this step's commit.

## Commit

`test(icoder): add autocomplete snapshot tests`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md for full context, then implement Step 7.

1. Verify existing test_snapshots.py ICoderApp(app_core) fixture still passes after Step 5 wiring (constraint I6). Regenerate existing baselines if needed.
2. Add three snapshot tests to tests/icoder/test_snapshots.py following the existing pattern
3. Each test types into InputArea and pauses for the dropdown to render
4. Generate baselines with: pytest tests/icoder/test_snapshots.py --snapshot-update -k autocomplete
5. Verify the generated SVGs look correct and contain no sensitive data
6. If the dropdown is cut off, adjust the terminal size or max-height CSS
7. Run all five quality checks — all must pass
8. Commit: "test(icoder): add autocomplete snapshot tests"
```
