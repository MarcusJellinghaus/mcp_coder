# Step 1 — Fix langchain tool output extraction

> See [summary.md](summary.md) for full context on issue #897.

## Goal

Replace `str(output)` in the `on_tool_end` handler with cascading content extraction
so tool results render as clean strings instead of pydantic repr.

## WHERE

- **Source:** `src/mcp_coder/llm/providers/langchain/agent.py` — lines 530-548
- **Tests:** `tests/llm/providers/langchain/test_langchain_agent_streaming.py` — `TestRunAgentStream` class

## WHAT

No new functions. Inline extraction logic before the two `str(output)` usage sites (lines 538, 546).
Store result in a local `result_text` variable, use it in both places.

## HOW

- `json` is already imported in `agent.py` (line 11) — no new imports needed.
- Use `hasattr`-based duck typing (not `isinstance`) to avoid importing `ToolMessage`.
- The existing `output_mock = MagicMock()` in the test gets `str(MagicMock())` as output —
  update the existing test and add new parametrized tests for the 4 extraction cases.

## ALGORITHM (extraction cascade)

```
output = event["data"]["output"]
if hasattr(output, "artifact") and isinstance(output.artifact, dict):
    sc = output.artifact.get("structured_content")
    if sc is not None:
        result_text = json.dumps(sc)
    else: fall through
if not yet resolved and hasattr(output, "content") and isinstance(output.content, list):
    result_text = "\n".join(b["text"] for b in output.content if isinstance(b, dict) and b.get("type") == "text")
elif not yet resolved and hasattr(output, "content") and isinstance(output.content, str):
    result_text = output.content
else:
    result_text = str(output)
```

Then replace both `str(output)` at lines 538 and 546 with `result_text`.

## DATA

The `result_text` string replaces the pydantic repr in:
- `tool_results_list[i]["output"]` — used for session history / `--continue-session`
- Yielded `StreamEvent` `{"type": "tool_result", "output": result_text, ...}` — consumed by renderer

## Tests (TDD — write first)

Add to `TestRunAgentStream` in `test_langchain_agent_streaming.py`:

1. **`test_tool_result_structured_content`** — Mock output with `artifact={"structured_content": {"result": True}}`.
   Assert yielded output is `'{"result": true}'`.

2. **`test_tool_result_content_blocks`** — Mock output with `content=[{"type": "text", "text": "hello"}]` (as a real list, not MagicMock).
   Assert yielded output is `"hello"`.

3. **`test_tool_result_content_string`** — Mock output with `content="plain text"` (a real string, not MagicMock).
   Assert yielded output is `"plain text"`.

4. **`test_tool_result_fallback`** — Mock output with no `artifact`, no `content`.
   Assert yielded output is `str(output_mock)`.

5. **Update `test_tool_result_from_on_tool_end`** — Add assertion on `tool_results[0]["output"]`
   to verify it's not the raw pydantic repr.

Each test follows the existing pattern: build `events` list → `_patch_run_agent_stream(events)` →
collect async results → filter `tool_result` events → assert `output` field.

## Commit

```
fix: extract clean content from langchain ToolMessage (#897)

Replace str(output) with cascading extraction:
artifact.structured_content → content blocks → string → fallback.
```
