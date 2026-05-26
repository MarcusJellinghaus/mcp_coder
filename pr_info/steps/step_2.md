# Step 2 — `is_error` propagation across providers + `ToolResult.is_error`

## Goal

Surface tool-error state from upstream providers so the renderer can show `→ error` in tier-1 and `(error)` in the detail-modal footer. Today all three providers drop `is_error` at emit time.

## WHERE

- `src/mcp_coder/llm/formatting/render_actions.py` — add `is_error: bool = False` to `ToolResult`
- `src/mcp_coder/llm/types.py` — `StreamEvent` docstring: document optional `is_error: bool` on `tool_result`
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — propagate `is_error` from `tool_use_result` block
- `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` — propagate `is_error` from `tool.execution_complete` status
- `src/mcp_coder/llm/providers/langchain/agent.py` — detect tool errors by inspecting the `on_tool_end` event's `data.output` (a `ToolMessage` with `status == 'error'` indicates a failed tool) and emit `tool_result(is_error=True)` accordingly. Before implementing, run a 5-line spike against `langchain_core.agents` `astream_events` v2 to confirm the exact key path (`event['data']['output'].status` vs `event['data']['output']['status']`).
- `src/mcp_coder/llm/formatting/stream_renderer.py` — read `is_error` from the event and set it on the returned `ToolResult`; also extend `_render_tool_output` return tuple from `(lines, total)` to `(lines, total, truncated)`
- Also extend `_render_tool_output` return tuple from `(lines, total)` to `(lines, total, truncated)` — internal change, no public API. `truncated = total > _TRUNCATION_THRESHOLD` (the helper already knows this internally). Update the helper's two existing call sites in `stream_renderer.py` to discard or use the new field. The new field is consumed by step 9's `_handle_stream_event` ToolResult branch.
- Tests in `tests/llm/formatting/test_stream_renderer.py`, `tests/llm/providers/claude/test_claude_cli_stream_parsing.py`, `tests/llm/providers/copilot/test_copilot_cli_streaming.py`, `tests/llm/providers/langchain/test_langchain_agent_streaming.py`

## WHAT

```python
# render_actions.py
@dataclass(frozen=True)
class ToolResult:
    name: str
    output_lines: list[str]
    total_lines: int
    truncated: bool
    is_error: bool = False   # NEW
```

Provider emitters: each `yield {"type": "tool_result", ...}` line gains an `"is_error": <bool>` entry.

- **Claude**: read `block.get("is_error", False)` from the `tool_use_result` block (claude_code_cli_streaming.py:58–63).
- **Copilot**: derive from the `tool.execution_complete` message's status field — set `True` if status indicates failure (e.g. `status == "error"`); else `False` (copilot_cli_streaming.py:68–73).
- **Langchain**: detect tool errors inside the existing `on_tool_end` branch by inspecting `event['data']['output']` — when it is a `ToolMessage` with `status == 'error'`, emit `tool_result` with `is_error=True` and an output string sourced from the message content. Do NOT raise — let the stream continue. Before implementing, run a 5-line spike against `langchain_core.agents` `astream_events` v2 to confirm the exact key path (`event['data']['output'].status` vs `event['data']['output']['status']`).

`StreamEventRenderer.render()`: when handling `tool_result`, read `event.get("is_error", False)` and pass through to `ToolResult(..., is_error=...)`.

`_render_tool_output(output, *, format_tools, full)`: extend the return signature from `(lines, total)` to `(lines, total, truncated)` where `truncated = total > _TRUNCATION_THRESHOLD` (already computed internally — just expose it). Update the helper's two existing call sites in `stream_renderer.py` to destructure the 3-tuple (discard or use `truncated` as appropriate). Step 9 consumes the new `truncated` field when computing the pre-rendered triple at `tool_result` time.

## HOW

- Default value `False` preserves backward compatibility for any caller building `ToolResult` directly.
- `StreamEvent` is a typed dict allowing extra keys — no schema migration needed.
- The langchain `on_tool_end` branch must still update `tool_results_list` so the history reconstruction at line 593 still includes the failed tool.

## ALGORITHM (langchain on_tool_end with error detection)

```
event_kind == "on_tool_end":
    run_id = event["run_id"]
    name   = event["name"]
    output_obj = event["data"]["output"]    # spike: confirm shape vs. ToolMessage
    is_error = getattr(output_obj, "status", None) == "error"
    output_text = getattr(output_obj, "content", str(output_obj))
    tool_call_id = run_id
    tool_results_list.append({"name": name, "output": output_text, "tool_call_id": tool_call_id, "run_id": run_id})
    yield {"type": "tool_result", "name": name, "output": output_text,
           "tool_call_id": tool_call_id, "is_error": is_error}
```

## DATA

- `is_error: bool` on the `tool_result` `StreamEvent` (optional, default `False`)
- `ToolResult.is_error: bool = False`

## TDD

1. `tests/llm/formatting/test_stream_renderer.py::test_tool_result_propagates_is_error` — feed event `{"type":"tool_result", "is_error": True, ...}` → `ToolResult.is_error == True`
2. `tests/llm/formatting/test_stream_renderer.py::test_tool_result_defaults_is_error_false` — no `is_error` key → `False`
3. `tests/llm/providers/claude/test_claude_cli_stream_parsing.py::test_tool_use_result_is_error_propagates` — fixture block with `is_error: True` → emitted event carries it
4. `tests/llm/providers/copilot/test_copilot_cli_streaming.py::test_tool_execution_complete_error_status` — fake `tool.execution_complete` with error status → `is_error: True` in emitted event
5. `tests/llm/providers/langchain/test_langchain_agent_streaming.py::test_on_tool_end_error_status_emits_tool_result_with_is_error` — mock astream_events delivering `on_tool_end` whose `data.output` is a `ToolMessage` with `status == "error"` → `tool_result` event with `is_error: True`; stream continues (no raise)

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green. Pytest must include the langchain provider test (run without exclusion for that file).

## LLM Prompt

> Implement **Step 2** from `pr_info/steps/step_2.md` (`is_error` propagation).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Add `is_error: bool = False` to `ToolResult` render-action (preserves existing constructors).
> - Update `StreamEvent` docstring in `llm/types.py`.
> - Three provider edits — claude, copilot, langchain. The langchain change detects errors inside `on_tool_end` by inspecting `event['data']['output']` (a `ToolMessage` with `status == 'error'`) and yields a `tool_result` event with `is_error=True` **instead of** raising. Run a 5-line spike against `langchain_core.agents` `astream_events` v2 first to confirm the exact key path.
> - TDD: add the four test cases first, then implement.
> - Do not change any other renderer state — that's step 4.
>
> All three quality gates green after the change.
