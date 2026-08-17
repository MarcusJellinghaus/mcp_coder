# Step 3 — Text paths adopt the shared helpers

**Goal:** Converge sites 1 and 2 of 4 (`_ask_text`, `_ask_text_stream`). Behaviour is
unchanged — the shared serializer produces byte-identical output to today's inline dump
loops — but the text path is now the same code as the agent path will be.

`_ask_text_stream` is the path `mcp-coder prompt` actually runs, so it is the site the
`--add-system-prompts` repro exercises.

## WHERE

* Modify `src/mcp_coder/llm/providers/langchain/__init__.py` — `_ask_text` (~lines
  296–370) and `_ask_text_stream` (~lines 629–685)
* Create `tests/llm/providers/langchain/test_langchain_multi_turn.py`

## WHAT

No signature changes. Both functions replace their inline assemble block and their
~10-line dump loop with:

```python
lc_messages = assemble_messages(system_messages, history, question)
...
store_langchain_history(session_id, serialize_messages(lc_messages + [ai_msg]))
```

## HOW

* Module-level import in `__init__.py`:
  `from ._messages import assemble_messages, serialize_messages`
  (safe — `_messages` has no intra-package imports).
* `_ask_text`: drop the deferred `from langchain_core.messages import HumanMessage,
  messages_from_dict` (no longer used) and the `history_messages` local.
* `_ask_text_stream`: reduce its deferred import to `AIMessage` only — it still builds
  the final `AIMessage(content=full_text)` from the accumulated deltas.
* Everything else (error handling, `_extract_usage`, 404 hints, timeout watchdog, event
  yielding) is untouched.

## ALGORITHM

```
history      = load_langchain_history(session_id)
lc_messages  = assemble_messages(system_messages, history, question)
ai_msg       = <invoke or stream-then-build AIMessage>
serialize_messages(lc_messages + [ai_msg])  # strips the leading system(s)
store_langchain_history(session_id, <that>)
```

Because `serialize_messages` strips leading systems, the stored list is exactly today's
`history + human + ai` — no behaviour change, one less place to get it wrong.

## DATA

Stored history: `list[dict[str, Any]]`, entries `{"type","data"}`, **no** `"system"`
entries. `LLMResponseDict` / `StreamEvent` output shapes are unchanged.

## Tests (write first)

New file `tests/llm/providers/langchain/test_langchain_multi_turn.py` — the multi-turn
text-path test required by the issue. It must drive the **streaming** text path
(`ask_langchain_stream` without `mcp_config`), because that is what `prompt` uses.

```python
class TestTextPathMultiTurn:
    def test_two_turns_store_no_system_messages_and_send_one(self) -> None: ...
```

Setup: a dict-backed fake for `load_langchain_history` / `store_langchain_history`
patched at `mcp_coder.llm.providers.langchain.<name>`, a `MagicMock` chat model whose
`.stream()` returns one chunk, `_load_langchain_config` and `_create_chat_model` patched
as in the existing tests. Drive two turns with the same `session_id` and both
`system_prompt=` and `project_prompt=` set.

Assertions:

* every stored entry has `entry["type"] != "system"` (both turns);
* `mock_model.stream.call_args_list` — each call's message list contains **exactly one**
  `SystemMessage` and it is at index 0;
* turn 2's message list contains the turn-1 human + AI messages (history really is
  reloaded, so the "no systems" result is not vacuous).

Existing tests in `test_langchain_provider_system_messages.py`,
`test_langchain_provider.py` and `test_langchain_streaming.py` must stay green
unchanged — that is the proof the serializer output is byte-identical.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3 only: make _ask_text and _ask_text_stream in
src/mcp_coder/llm/providers/langchain/__init__.py use assemble_messages() and
serialize_messages() from ._messages, and add
tests/llm/providers/langchain/test_langchain_multi_turn.py with the multi-turn text-path
test described in the step file (it must run through the STREAMING text path).

Write the new test first. Do not touch agent.py in this step. Existing text-path tests
must stay green without modification — if one needs changing, stop and report, because
that means the serialized output is no longer byte-identical.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```
