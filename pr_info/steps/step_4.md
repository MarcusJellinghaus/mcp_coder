# Step 4 — `StreamEventRenderer` pending-tool FIFO + `cleanup_pending()`

## Goal

Make the renderer pair each `tool_use_start` with its `tool_result` to compute `duration_ms`. Add `cleanup_pending()` so the app layer can synthesize cancelled results for orphans on cancel and on `StreamDone`.

## WHERE

- `src/mcp_coder/llm/formatting/stream_renderer.py` — add `_pending` FIFO state + `cleanup_pending()`; update class docstring (no longer stateless)
- `src/mcp_coder/llm/formatting/render_actions.py` — add `duration_ms: int | None = None` and `raw_name: str` to `ToolResult`
- `tests/llm/formatting/test_stream_renderer.py` — pairing and cleanup tests

## WHAT

```python
# render_actions.py
@dataclass(frozen=True)
class ToolResult:
    name: str            # display name (existing)
    raw_name: str        # NEW — raw tool name (matches ToolStart raw key for FIFO lookup)
    output_lines: list[str]
    total_lines: int
    truncated: bool
    is_error: bool = False
    duration_ms: int | None = None   # NEW

# stream_renderer.py
class StreamEventRenderer:
    def __init__(self, *, format_tools: bool = True) -> None:
        self._format_tools = format_tools
        self._pending: deque[tuple[str, float]] = deque()   # (raw_name, monotonic_start)

    def render(self, event: StreamEvent) -> RenderAction | None: ...

    def cleanup_pending(self) -> list[ToolResult]:
        """Synthesize cancelled-result actions for every orphaned tool start.
        Clears the FIFO. Called on cancellation and on StreamDone by the app layer.
        """
```

## HOW

- On `tool_use_start`: `self._pending.append((raw_name, time.monotonic()))`; return `ToolStart(...)` as today.
- On `tool_result`:
  - Walk `self._pending` left-to-right; pop the **first** entry whose name matches `event["name"]`.
  - If found, `duration_ms = int((time.monotonic() - start) * 1000)`; else `None`.
  - Build and return `ToolResult(..., raw_name=event["name"], is_error=..., duration_ms=...)`. The raw name is propagated so the app layer can FIFO-match results to open tool units (step 9).
- `cleanup_pending()`:
  - For each `(name, _start)` left in the FIFO, build `ToolResult(name=_format_tool_name(name), raw_name=name, output_lines=["(cancelled)"], total_lines=1, truncated=False, is_error=True, duration_ms=None)`. The original raw `name` is preserved on `raw_name` so the caller can locate the matching open tool unit via the per-name FIFO.
  - Clear the FIFO. Return the list (in FIFO order).
- Update class docstring: state that the renderer is stateful (pending FIFO) and that callers MUST invoke `cleanup_pending()` on cancellation and on `StreamDone`.

## ALGORITHM (pairing)

```
on tool_use_start:
    pending.append((name, monotonic()))
    return ToolStart(...)

on tool_result:
    duration = None
    for i, (n, t0) in enumerate(pending):
        if n == event_name:
            del pending[i]   # O(N) but N is tiny
            duration = int((monotonic() - t0) * 1000)
            break
    return ToolResult(..., raw_name=event_name, duration_ms=duration)
```

## DATA

- `_pending: deque[tuple[str, float]]` — raw tool name + monotonic start time
- `cleanup_pending()` returns `list[ToolResult]` (empty when FIFO is empty)

## TDD

Tests in `tests/llm/formatting/test_stream_renderer.py`:

1. `test_pairs_start_and_result_computes_duration` — emit start, sleep tiny, emit result → `duration_ms` is a positive int
2. `test_unmatched_result_has_none_duration` — emit only `tool_result` → `duration_ms is None`
3. `test_interleaved_pairing_by_name` — start_A, start_B, result_B, result_A → both paired correctly
4. `test_cleanup_pending_synthesizes_cancelled_results` — start, no result, call `cleanup_pending()` → returns one `ToolResult(is_error=True, output_lines=["(cancelled)"])`; second call returns `[]`
5. `test_stream_done_does_not_auto_clean` — calling `render({"type":"done"})` does NOT clear FIFO (app does it explicitly via `cleanup_pending`)
6. `test_renderer_state_survives_across_turns` — start in turn 1, result in turn 2 → still paired (warns the implementer about the FIFO lifetime risk; documents the explicit need for cleanup on `done`)
7. `test_tool_result_carries_raw_name` — covers BOTH paths:
   - Live: feed `tool_use_start(name="Bash")` then `tool_result(name="Bash", ...)` → returned `ToolResult.raw_name == "Bash"` (matches the event's raw name, not the display name).
   - Cancelled: feed `tool_use_start(name="Bash")`, no result, call `cleanup_pending()` → returned synthesized `ToolResult.raw_name == "Bash"` (preserved from the pending FIFO entry).

Then implement. Update existing tests that constructed `ToolResult` to either accept the new default `duration_ms=None` and supply `raw_name=...` or pass them explicitly.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 4** from `pr_info/steps/step_4.md` (renderer FIFO + cleanup).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - `StreamEventRenderer` becomes stateful — update its class docstring.
> - `cleanup_pending()` returns `list[ToolResult]`; does NOT auto-fire — app layer calls it on cancel AND on `StreamDone` in step 9.
> - Use `time.monotonic()`. Per-tool-name FIFO matching (positional within same name).
> - Add `duration_ms: int | None = None` and `raw_name: str` to `ToolResult` render-action. Populate `raw_name=event["name"]` for live results and `raw_name=name` (the raw FIFO key) for synthesized cancelled results.
> - TDD: 7 test cases first, then implement.
>
> All three quality gates green after the change.
