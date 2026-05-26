# Plan-review Decisions Log

Round 2 plan-review (supervisor-accepted changes applied 2026-05-26).

## R2-01 — `ToolResult.raw_name` field

Add `raw_name: str` to the `ToolResult` render-action (Step 4) alongside the existing `name: str` display field. The renderer populates `raw_name=event["name"]` for live results and `raw_name=name` (the raw FIFO key) for synthesized cancelled results. Step 9 then uses `result.raw_name` / `cancelled.raw_name` for `_open_tool_units` lookups — the deque is keyed by raw tool name.

**Rationale:** `_open_tool_units: dict[str, deque[str]]` is keyed by raw name; the action needs to carry the raw key explicitly rather than reconstruct or alias it.

## R2-02 — `ContentUnit` pre-rendered tool body fields (user Q5 decision = A)

`ContentUnit` gains three tool-only fields populated once at `tool_result` time:

- `output_lines: tuple[str, ...] = ()` — pre-rendered, already-truncated body lines (tier 2)
- `total_lines: int = 0` — total line count (drives the `(N lines, …ms)` footer)
- `truncated: bool = False` — head/tail truncation flag

The existing `output: str` field carries the FULL untruncated output for the tier-3 modal. The pre-rendered triple is computed at write time using `_render_tool_output(...)` and read by `_render_unit_atomic` — no `format_tools` plumbing into `OutputLog`.

**Rationale:** decouples truncation (a view concern) from storage; the modal needs the full text, tier-2 needs the truncated text, both should be available without recomputing on every rebuild.

## R2-03 — `format_tool_compressed` takes explicit fields

`format_tool_compressed()` signature changes from `(start: ToolStart, result: ToolResult)` to explicit fields: `(name, args, output_lines, total_lines, truncated, duration_ms, is_error)`. Both `_render_unit_atomic` and the live `tool_result` branch call it with `ContentUnit` field values directly — no `ToolResult` synthesis required.

**Rationale:** synthesizing a `ToolResult` from `ContentUnit` fields just to call a formatter is ceremony with no benefit; explicit fields read cleaner at call sites.

## R2-04 — `_render_unit_atomic` for in-flight tools renders start lines only

When `unit.kind == "tool"` and `unit.output_lines` is empty (in-flight, no result yet), `_render_unit_atomic` returns only the start lines via `format_tool_start`. The `└ done` footer does not appear until `update_unit_and_rerender` populates `output_lines`. Covered by new test `test_rebuild_with_pending_tool_renders_start_only`.

## R2-05 — Cancel-path ordering (explicit)

Inside `_stream_llm`'s `finally` block on cancellation, the sequence is now fixed and documented:

1. `_flush_buffer()`
2. `finalize_turn()`
3. `cleanup_pending()` → synthesize cancelled `ToolResult`s
4. For each cancelled result: update the matching open tool unit via `_open_tool_units.get(cancelled.raw_name)`
5. `_append_cancelled_marker()`
6. `reset_busy()`
7. blank line

**Rationale:** the cancelled marker (5) must come AFTER orphan-unit updates (4) so the user sees "tool block patched to cancelled, then the marker" — not the reverse.

## R2-06 — `clear_state` rename owned by Step 5

Step 5 owns the `clear_recorded() → clear_state()` rename and all call-site updates in `app.py` (`on_input_area_input_submitted`, `do_resume`). Step 1's UI dispatch case for `ClearOutput` calls `output.clear_state()` from the start (step 1's HOW now says "see step 5 for the rename" rather than "renamed to clear_state() in step 5"). Step 9 does NOT touch this rename.

## R2-07 — Soft-assert remaining `_open_tool_units` deques

Replaced the silent `for dq in self._open_tool_units.values(): dq.clear()` defensive sweep with a WARN-log loop that surfaces FIFO desync bugs:

```python
for raw_name, dq in self._open_tool_units.items():
    if dq:
        log.warning("FIFO desync: %d open tool units remain for %s after cleanup", len(dq), raw_name)
        dq.clear()
```

**Rationale:** silent recovery hides real bugs (renderer FIFO and app FIFO falling out of sync); a WARN log preserves recovery behavior while making the desync observable in production.

## R2-08 — Click coordinates: commit to `event.y + self.scroll_offset.y`

Removed the optional `event.style.meta` path and the associated 5-line spike from Step 8. `RichLog` does not currently set `Strip` metadata, so the meta-based path is not viable. Step 8 commits to `clicked_line = event.y + self.scroll_offset.y` outright.

## R2-09 — `tool_result` rebuild perf trade-off (v1 accepted)

Documented in Step 9's new "Performance note" section: every `tool_result` event triggers a full `rebuild()`. For long sessions this is O(n) re-renders. **Accepted for v1** — measure in practice before optimizing. Future optimization path: `update_unit_and_rerender(..., rerender=False)` flag so cancel-path bulk updates rebuild once at the end.

## R2-10 — New TDD tests added

- Step 4: `test_tool_result_carries_raw_name` (covers live + cancelled paths)
- Step 5: `test_append_unit_assistant_turn_with_empty_lines_no_script_entry`
- Step 6: `test_rebuild_with_pending_tool_renders_start_only`

## R3-01 — `_render_tool_output` returns 3-tuple

Extend the helper signature from `(lines, total)` to `(lines, total, truncated)` where `truncated = total > _TRUNCATION_THRESHOLD` (already computed internally). Step 2 owns the change (bundled with the `is_error` propagation work since both touch `stream_renderer.py`). Caller in step 9's `_handle_stream_event` ToolResult branch destructures the 3-tuple to populate `ContentUnit.truncated`. Step 7's modal also updates its destructure (discards the new field with `_truncated`). Existing internal call sites in `stream_renderer.py` are updated to discard the new field where unused.

## R3-02 — `rebuild()` implemented in step 5; tier dispatch added in step 6

Step 5 ships a minimal `rebuild()` (non-tier — tools always render compressed) so `update_unit_and_rerender` is functional from step 5 onward. The rebuild walk re-emits each `_script` entry: atomic entries (`(unit_id, None)`) go through `_render_unit_atomic(unit)`, streamed entries (`(unit_id, line)`) write the line literally. Step 6 then changes `_render_unit_atomic` to **dispatch on effective tier** — reading `_tool_tier_overrides.get(unit_id, _tool_display_default)` and returning `format_tool_oneline(...)` for tier 1 or the existing compressed body for tier 2. The rebuild walk itself does not change.

**Rationale:** the previous "may stub `rebuild()` to no-op until step 6" wording was a footgun — step 5 tests for `update_unit_and_rerender` need rendering to actually happen. Bundling the rebuild walk into step 5 keeps each step's deliverable self-testable.

## R3-03 — `output_lines`-driven body trigger (not full `output`)

Tool body lines in `_render_unit_atomic` are emitted when `unit.output_lines` is non-empty — NOT when `unit.output` is set. The pre-rendered triple (`output_lines`, `total_lines`, `truncated`) is the trigger; `output` is reserved for the modal's tier-3 view. Step 5 HOW updated accordingly.

## R3-04 — `format_tool_compressed` invocation is indirect from step 9

Step 9's `_handle_stream_event` ToolResult branch does NOT call `format_tool_compressed` directly. It calls `update_unit_and_rerender` which invokes `rebuild() → _render_unit_atomic → format_tool_compressed`. Step 6's WHERE / WHAT / LLM-prompt updated to soften the "both call this helper" language and document the indirect path explicitly. Byte-identical output is still guaranteed because the initial render and any rebuild both flow through `_render_unit_atomic`.

## R3-05 — Step 9 test #4 description tightened to dict-insertion-order semantics

The previous test #4 description (`test_tool_inside_turn_keeps_turn_open`) conflated two concerns. Rewritten as `test_last_unit_returns_most_recent_inserted_unit_dict_order` — explicitly locking F2 / "most recent content" to dict insertion order: subsequent `extend_open_unit` calls on a turn do NOT update `last_unit()`; only appending a new unit does. Matches the documented semantics in `summary.md`.

## R3-06 — Step 5 test #15 empty-turn → zero-output invariant

Test `test_append_unit_assistant_turn_with_empty_lines_no_script_entry` gains an explicit assertion: `rebuild()` produces zero buffer lines for an empty assistant_turn. No `(unit_id, None)` entry in `_script` means the rebuild walk skips it entirely. Locks the invariant that registering an empty turn unit costs zero render bytes.

## R3-07 — Step 5 test #13 payload now includes the pre-rendered triple

The example `update_unit_and_rerender` call in test #13 now passes `output_lines=("X",), total_lines=1, truncated=False` alongside `output="X"`, matching the actual call shape used by step 9. Tightens the spec → implementation contract.

## R4-01 — `format_tool_compressed` extraction moved from step 6 → step 5

Step 5's `_render_unit_atomic` test requires body rendering; the body comes from `format_tool_compressed`. Putting the extraction in step 6 created a backward cross-step dependency that broke "each step = one green commit" independence. The helper is now introduced in step 5; step 6 only adds tier-dispatch to `_render_unit_atomic`.

**Rationale:** preserves step-by-step independence — step 5 ships with all rendering helpers it depends on.

## R4-02 — `_tool_tier_overrides` declared in step 5

Field is introduced empty in step 5 so `clear_state()` can wipe it. Step 6 populates the field via `toggle_unit_tier()` and `set_tool_display_default()`. Step 5 does NOT introduce `_tool_display_default` — that field remains a step 6 addition along with the tier dispatch.

**Rationale:** closes a spec gap — `clear_state()` referenced a field not declared in the state-additions list.

## R5-01 — `format_tool_oneline` switched to explicit-fields signature

Step 3 originally defined `format_tool_oneline(start: ToolStart, result: ToolResult | None, duration_ms: int | None) -> str`. Step 6's atomic `_render_unit_atomic` had no `ToolStart`/`ToolResult` objects available and called it with explicit fields, causing a signature mismatch. Aligned by changing step 3's signature to explicit fields:

```python
def format_tool_oneline(*, name: str, args: dict[str, object], duration_ms: int | None, is_error: bool) -> str: ...
```

Status semantics: `duration_ms=None, is_error=False` → running; `duration_ms!=None, is_error=False` → done; `is_error=True` → error.

**Rationale:** Mirrors R2-03 (same fix for `format_tool_compressed`). Atomic rebuild has no upstream events; passing fields directly avoids synthesizing throwaway objects.
