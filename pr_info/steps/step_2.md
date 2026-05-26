# Step 2 — `is_error` propagation across providers + `ToolResult.is_error`

## Goal

Surface tool-error state from upstream providers so the renderer can show `→ error` in tier-1 and `(error)` in the detail-modal footer. Today all three providers drop `is_error` at emit time.

## WHERE

- `src/mcp_coder/llm/formatting/render_actions.py` — add `is_error: bool = False` to `ToolResult`
- `src/mcp_coder/llm/types.py` — `StreamEvent` docstring: document optional `is_error: bool` on `tool_result`
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — propagate `is_error` from `tool_use_result` block
- `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` — propagate `is_error` from `tool.execution_complete` status
- `src/mcp_coder/llm/providers/langchain/agent.py` — add `on_tool_error` event branch that emits `tool_result` with `is_error=True` (instead of raising and killing the stream)
- `src/mcp_coder/llm/formatting/stream_renderer.py` — read `is_error` from the event and set it on the returned `ToolResult`
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
- **Langchain**: add a new `elif event_kind == "on_tool_error":` branch around agent.py:530 that emits a `tool_result` event with `is_error=True` and an output string sourced from the exception. Do NOT raise — let the stream continue.

`StreamEventRenderer.render()`: when handling `tool_result`, read `event.get("is_error", False)` and pass through to `ToolResult(..., is_error=...)`.

## HOW

- Default value `False` preserves backward compatibility for any caller building `ToolResult` directly.
- `StreamEvent` is a typed dict allowing extra keys — no schema migration needed.
- The langchain `on_tool_error` branch must still update `tool_results_list` so the history reconstruction at line 593 still includes the failed tool.

## ALGORITHM (langchain on_tool_error)

```
event_kind == "on_tool_error":
    run_id = event["run_id"]
    name   = event["name"]
    error  = event["data"].get("error") or "(tool error)"
    tool_call_id = run_id
    tool_results_list.append({"name": name, "output": str(error), "tool_call_id": tool_call_id, "run_id": run_id})
    yield {"type": "tool_result", "name": name, "output": str(error),
           "tool_call_id": tool_call_id, "is_error": True}
```

## DATA

- `is_error: bool` on the `tool_result` `StreamEvent` (optional, default `False`)
- `ToolResult.is_error: bool = False`

## TDD

1. `tests/llm/formatting/test_stream_renderer.py::test_tool_result_propagates_is_error` — feed event `{"type":"tool_result", "is_error": True, ...}` → `ToolResult.is_error == True`
2. `tests/llm/formatting/test_stream_renderer.py::test_tool_result_defaults_is_error_false` — no `is_error` key → `False`
3. `tests/llm/providers/claude/test_claude_cli_stream_parsing.py::test_tool_use_result_is_error_propagates` — fixture block with `is_error: True` → emitted event carries it
4. `tests/llm/providers/copilot/test_copilot_cli_streaming.py::test_tool_execution_complete_error_status` — fake `tool.execution_complete` with error status → `is_error: True` in emitted event
5. `tests/llm/providers/langchain/test_langchain_agent_streaming.py::test_on_tool_error_emits_tool_result_with_is_error` — mock astream_events delivering `on_tool_error` → `tool_result` event with `is_error: True`; stream continues (no raise)

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
> - Three provider edits — claude, copilot, langchain. The langchain change adds an `on_tool_error` branch that yields a `tool_result` event with `is_error=True` **instead of** raising.
> - TDD: add the four test cases first, then implement.
> - Do not change any other renderer state — that's step 4.
>
> All three quality gates green after the change.
