# Step 1: Extend ResponseAssembler with tool_trace Accumulation

**Commit message:** `feat(types): add tool_trace accumulation to ResponseAssembler`

**References:** [summary.md](summary.md) — "ResponseAssembler Extension" section

## LLM Prompt

> Implement Step 1 from `pr_info/steps/step_1.md`.
> Read `pr_info/steps/summary.md` for full context (issue #603).
> Read the existing code in `src/mcp_coder/llm/types.py` and `tests/llm/test_types.py` before making changes.
> Follow TDD: write tests first, then implement, then run all three checks (pylint, pytest, mypy).

## WHERE

- `tests/llm/test_types.py` — add test class
- `src/mcp_coder/llm/types.py` — modify `ResponseAssembler`

## WHAT — Tests First

Add `TestResponseAssemblerToolTrace` class to `tests/llm/test_types.py`:

```python
class TestResponseAssemblerToolTrace:
    """ResponseAssembler accumulates tool events into tool_trace."""

    def test_tool_use_start_accumulated(self) -> None:
        """tool_use_start events appear in tool_trace."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "tool_use_start", "name": "read_file", "args": {"path": "x.py"}, "tool_call_id": "tc_1"})
        result = assembler.result()
        assert result["raw_response"]["tool_trace"] == [
            {"type": "tool_use_start", "name": "read_file", "args": {"path": "x.py"}, "tool_call_id": "tc_1"}
        ]

    def test_tool_result_accumulated(self) -> None:
        """tool_result events appear in tool_trace."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "tool_result", "name": "read_file", "output": "content", "tool_call_id": "tc_1"})
        result = assembler.result()
        assert result["raw_response"]["tool_trace"] == [
            {"type": "tool_result", "name": "read_file", "output": "content", "tool_call_id": "tc_1"}
        ]

    def test_full_tool_cycle_in_order(self) -> None:
        """tool_use_start + tool_result accumulate in order."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "tool_use_start", "name": "sleep", "args": {"s": 1}, "tool_call_id": "tc_1"})
        assembler.add({"type": "tool_result", "name": "sleep", "output": "ok", "tool_call_id": "tc_1"})
        result = assembler.result()
        trace = result["raw_response"]["tool_trace"]
        assert len(trace) == 2
        assert trace[0]["type"] == "tool_use_start"
        assert trace[1]["type"] == "tool_result"

    def test_empty_tool_trace_not_in_result(self) -> None:
        """When no tool events, tool_trace key is absent from raw_response."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "text_delta", "text": "hi"})
        assembler.add({"type": "done", "session_id": "s1", "usage": {}})
        result = assembler.result()
        assert "tool_trace" not in result["raw_response"]

    def test_tool_trace_with_text_deltas(self) -> None:
        """Tool events interleaved with text still accumulate correctly."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "text_delta", "text": "thinking..."})
        assembler.add({"type": "tool_use_start", "name": "run", "args": {}, "tool_call_id": "tc_1"})
        assembler.add({"type": "tool_result", "name": "run", "output": "done", "tool_call_id": "tc_1"})
        assembler.add({"type": "text_delta", "text": "Result is done."})
        result = assembler.result()
        assert result["text"] == "thinking...Result is done."
        assert len(result["raw_response"]["tool_trace"]) == 2
```

## WHAT — Implementation

Modify `ResponseAssembler` in `src/mcp_coder/llm/types.py`:

**Signature changes:**
- `__init__`: add `self._tool_trace: list[StreamEvent] = []`
- `add()`: handle `tool_use_start` and `tool_result` event types
- `result()`: include `tool_trace` in `raw_response` only if non-empty

## ALGORITHM (add() extension)

```
if event_type == "tool_use_start":
    self._tool_trace.append(event)
elif event_type == "tool_result":
    self._tool_trace.append(event)
```

## ALGORITHM (result() extension)

```
if self._tool_trace:
    raw_response["tool_trace"] = list(self._tool_trace)
```

## DATA

- `_tool_trace`: `list[StreamEvent]` — ordered list of tool events as received
- In `result()["raw_response"]["tool_trace"]`: same list, only present if non-empty

## HOW — Integration

- No new imports needed
- No changes to `StreamEvent` type alias (types already documented)
- Existing `test_response_assembler_tool_events` test remains valid (it checks `events` list, not `tool_trace`)

## Verification

Run all three checks after implementation:
1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
3. `mcp__tools-py__run_mypy_check`
