# Step 3: Multi-chunk snapshot test + regenerate all snapshot baselines

> **Context:** See `pr_info/steps/summary.md` for full issue background and design.
> **Prerequisite:** Steps 1–2 completed — buffer, Static widget, tests a–h all passing.

## Goal

Add one snapshot test (i) that locks the new `Static` streaming-tail layout with a multi-chunk response. Regenerate all existing snapshot baselines since the new `Static` widget changes the DOM for every snapshot.

## LLM Prompt

```
Implement Step 3 from pr_info/steps/step_3.md.
Read pr_info/steps/summary.md for context.
Read tests/icoder/test_snapshots.py before making changes.
Steps 1-2 are already implemented.
Add one new snapshot test for multi-chunk streaming.
Regenerate ALL snapshot baselines (the new Static widget changes the DOM).
Review regenerated SVGs for leaked paths/secrets/env vars.
Run all quality checks after changes.
```

## WHERE — Files to modify

| File | Action |
|---|---|
| `tests/icoder/test_snapshots.py` | Modify (add test) |
| `tests/icoder/__snapshots__/test_snapshots/*.svg` | Regenerate all baselines |

## WHAT — Changes

### 1. `tests/icoder/test_snapshots.py`

**New imports needed:**
```python
from mcp_coder.llm.types import StreamEvent
```

**New test (i) — snapshot for multi-chunk streaming:**

```python
def test_snapshot_multi_chunk_streaming(snap_compare: Any, tmp_path: Path) -> None:
    """Snapshot: multi-chunk streaming response with line breaks."""
    responses: list[list[StreamEvent]] = [[
        {"type": "text_delta", "text": "Hello "},
        {"type": "text_delta", "text": "world!\n"},
        {"type": "text_delta", "text": "Second line."},
        {"type": "done"},
    ]]
    fake_llm = FakeLLMService(responses=responses)
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(llm_service=fake_llm, event_log=event_log)
        app = ICoderApp(app_core)

        async def send_message(pilot: Any) -> None:
            input_area = app.query_one(InputArea)
            input_area.focus()
            await pilot.pause()
            input_area.insert("test streaming")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(delay=0.5)

        assert snap_compare(app, run_before=send_message)
```

Note: This test creates its own `ICoderApp` with custom responses instead of using the `icoder_app` fixture (which uses default single-chunk FakeLLMService).

### 2. Regenerate all snapshot baselines

Run on Windows:
```bash
pytest tests/icoder/test_snapshots.py --snapshot-update
```

This may regenerate up to all 8 existing SVGs + the 1 new one because the `Static(id="streaming-tail")` widget added in Step 1 changes the rendered DOM for every test.

**Note on `height: auto`:** The empty `Static#streaming-tail` may collapse to 0 lines in non-streaming snapshots, in which case some baselines may not actually differ. After `--snapshot-update`, run:
```bash
git diff --stat tests/icoder/__snapshots__/
```
and only commit baselines that genuinely changed — discard no-op regenerations.

### 3. Review regenerated SVGs

**Baseline diff review (mandatory):** For each regenerated SVG, diff it against the previously committed baseline. The ONLY expected visual change is the addition of the `Static#streaming-tail` row (likely an empty row) between `OutputLog` and the input area. Any other pixel-level change — colors, wrapping, unrelated widgets, font metrics — must be investigated and justified before committing.

Also verify:
- No local file paths (e.g. `C:\Users\...`) leaked into SVGs
- No environment variables or secrets visible
- No API keys or tokens
- Layout looks correct (Static tail is visible but empty in non-streaming snapshots)

## HOW — Integration

- The new test follows the exact same pattern as `test_snapshot_after_conversation` but with explicit multi-chunk responses
- `snap_compare` is provided by `pytest-textual-snapshot` (already a dev dependency)
- The `pytestmark` on the module already applies `skipif(not win32)` and `textual_integration`

## Commit message

```
test(icoder): add multi-chunk streaming snapshot + regenerate baselines (#735)

Add snapshot test (i) locking the Static streaming-tail layout with
multi-chunk response containing newlines.

Regenerate all snapshot baselines — the new Static widget in the DOM
changes every existing snapshot's rendered output.
```
