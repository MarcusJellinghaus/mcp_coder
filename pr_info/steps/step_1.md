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
result_text = None
if hasattr(output, "artifact") and isinstance(output.artifact, dict):
    sc = output.artifact.get("structured_content")
    if sc is not None:
        result_text = json.dumps(sc)
if result_text is None and hasattr(output, "content"):
    if isinstance(output.content, list):
        result_text = "\n".join(b["text"] for b in output.content if isinstance(b, dict) and b.get("type") == "text")
    elif isinstance(output.content, str):
        result_text = output.content
if result_text is None:
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

2. **`test_tool_result_content_blocks`** — Parameterized (or two variants) covering:
   - Variant A: `content=[{"type": "text", "text": "hello"}]` → assert output is `"hello"`
   - Variant B: `content=[{"type": "text", "text": "line1"}, {"type": "image", "url": "..."}, {"type": "text", "text": "line2"}]` → assert output is `"line1\nline2"` (non-text blocks filtered out)

3. **`test_tool_result_content_string`** — Mock output with `content="plain text"` (a real string, not MagicMock).
   Assert yielded output is `"plain text"`.

4. **`test_tool_result_artifact_without_structured_content`** — Mock output with
   `artifact={"other_key": "value"}` and `content="fallback text"`. Assert output is
   `"fallback text"` (verifies cascade falls through from artifact to content).

5. **`test_tool_result_fallback`** — Mock output with no `artifact`, no `content`.
   Assert yielded output is `str(output_mock)`.

6. **Update `test_tool_result_from_on_tool_end`** — Set the mock output's attributes
   (e.g., `output_mock.content = "test result"`) so it exercises the content-string
   extraction path, and assert `tool_results[0]["output"] == "test result"`.

Each test follows the existing pattern: build `events` list → `_patch_run_agent_stream(events)` →
collect async results → filter `tool_result` events → assert `output` field.

## Commit

```
fix: extract clean content from langchain ToolMessage (#897)

Replace str(output) with cascading extraction:
artifact.structured_content → content blocks → string → fallback.
```
