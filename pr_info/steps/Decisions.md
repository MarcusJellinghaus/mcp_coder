# Plan Decisions (Issue #819)

Decisions made during the technical-lead review of the implementation plan.

## D1. Usage helpers live in `_usage.py` submodule

**Decision:** `_extract_usage()` and `_sum_usage()` go into a new
`src/mcp_coder/llm/providers/langchain/_usage.py` file rather than into
`langchain/__init__.py`.

**Rationale:** `agent.py` needs to import the helpers, and `langchain/__init__.py`
also needs them. Placing them in `__init__.py` creates circular-import risk between
`langchain/__init__.py` and `agent.py`. A dedicated submodule imported by both avoids
this.

**Affects:** step_4.md (create file), step_5.md (import path), summary.md.

## D2. `_sum_usage` always returns all 4 keys

**Decision:** Change `_sum_usage` semantics from "drop keys where sum == 0" to
"always include all 4 keys with 0 default".

**Rationale:** Symmetric with `_extract_usage` (extraction conditionally populates;
summing unconditionally propagates). The display layer already gates `cache:XX%`
on `cache_read > 0`, so emitting zeros is safe and simplifies reasoning.

**Affects:** step_4.md (`_sum_usage` algorithm).

## D3. Helper signatures use `UsageInfo` type, not `dict[str, int]`

**Decision:** `_extract_usage()` and `_sum_usage()` return `UsageInfo`
(imported from `mcp_coder.llm.types`).

**Rationale:** Consistency with the provider-agnostic contract defined in step 1.
`UsageInfo` is a `TypedDict` so it is assignment-compatible with `dict[str, int]`
at runtime while providing richer type information.

**Affects:** step_4.md, step_5.md.

## D4. `display_text()` must guard against `ZeroDivisionError`

**Decision:** Add a test `update(input=0, output=0, cache_read=100)` \u2192 cache% hidden,
no exception raised.

**Rationale:** A provider may theoretically emit `cache_read > 0` while
`input_tokens == 0`. The cache% branch must check `last_input > 0` (not just
`last_cache_read > 0`) to avoid a crash.

**Affects:** step_2.md (new test case #7).

## D5. Streaming usage tracking is last-wins across any chunk

**Decision:** In `_ask_text_stream`, track any chunk carrying non-empty
`usage_metadata` as `last_chunk` (last-wins). Do not assume usage only appears
on the final chunk.

**Rationale:** Some providers emit usage on a middle chunk and then emit further
chunks without usage_metadata. A "final chunk only" assumption would drop usage
silently. Added a regression test (middle chunk has usage, final chunk does not).

**Affects:** step_4.md (algorithm note, test #9).

## D6. Agent tests use real `AIMessage` objects, not `Mock`

**Decision:** `test_run_agent_stats_include_usage` (and peers) must construct
real `langchain_core.messages.AIMessage(content=..., usage_metadata={...})`
instances rather than `Mock(spec=...)`.

**Rationale:** `Mock` with `usage_metadata` attribute does not necessarily mirror
real attribute access semantics (`getattr(ai_msg, "usage_metadata", None)`), and
a real `AIMessage` is the exact object `ainvoke()` returns in production.

**Affects:** step_5.md (test #1 description).

## D7. Drop stale line-number references

**Decision:** Replace "lines 91-95"-style references with symbolic references
(function/branch names) throughout step files.

**Rationale:** Line numbers drift as the codebase evolves; symbolic references
survive refactors and reduce plan-maintenance burden.

**Affects:** step_3.md.

## D8. Add Claude CLI \u2192 icoder regression test

**Decision:** Add `test_stream_llm_claude_cli_done_event_cache_regression` to step 3.

**Rationale:** The Claude CLI pipeline currently emits `cache_read_input_tokens`
through `_map_stream_message_to_event`, but no dedicated test exercises that
field end-to-end through `AppCore`. A regression guard prevents silent breakage.

**Affects:** step_3.md (new test #4).

## D9. `cache_creation_input_tokens` is captured but not displayed

**Decision:** Document in `summary.md` that `cache_creation_input_tokens` flows
through `StreamEvent["usage"]` and `raw_response["usage"]` but is NOT extracted
into `TokenUsage` or displayed in the icoder status bar.

**Rationale:** Clarifies scope for future maintainers. The field is preserved
for analysis/logging without adding UI noise now.

**Affects:** summary.md.

## D10. Clarify `_ask_text_stream` patch location (round 2)

**Decision:** Step 4 must specify that `last_chunk` tracking and the modified
`yield done` go inside the existing `try:` block (tracking inside the
`for chunk in chat_model.stream(...)` loop; done-event replacement after the
loop). Error/timeout branches are unchanged.

**Rationale:** Prevents the implementer from accidentally patching the error
path or introducing a duplicate done event outside the try block.

**Affects:** step_4.md.

## D11. Clarify `run_agent_stream` done event shape (round 2)

**Decision:** Step 5 must note that the existing `run_agent_stream` done event
is `yield {"type": "done", "session_id": session_id}` (NO `usage` key), unlike
`_ask_text_stream` which already has `"usage": {}`. Step 5 is the commit that
adds the `usage` key to `run_agent_stream`'s done event.

**Rationale:** Avoids confusion about whether step 5 is "filling an empty dict"
vs. "adding a new key". It is the latter.

**Affects:** step_5.md.

## D12. Parameterize `test_extract_usage_no_metadata` (round 2)

**Decision:** Split/parameterize `test_extract_usage_no_metadata` to cover three
distinct inputs: (a) attribute absent on message, (b) `usage_metadata is None`,
(c) `usage_metadata == {}`. All three must return `{}`.

**Rationale:** The production code uses
`getattr(ai_msg, "usage_metadata", None) or {}`. All three inputs hit a
different code path in that expression; one generic test would leave two of
them unverified.

**Affects:** step_4.md (test #2).

## D13. Add `ResponseAssembler` end-to-end test for all 4 usage fields (round 2)

**Decision:** Add `test_ask_text_stream_usage_flows_to_raw_response` to step 4:
exercise `_ask_text_stream()` end-to-end through `ResponseAssembler` (via
`ask_with_provider(..., provider_stream=True)` or directly). Assert all 4
fields (including `cache_creation_input_tokens`) land in
`LLMResponseDict.raw_response["usage"]`.

**Rationale:** `tests/llm/test_types.py::test_response_assembler_done_event`
already tests the assembler in isolation with 2 fields
(`input_tokens`, `output_tokens`). A LangChain-path test with all 4 fields
closes the gap and guards against regression in the `_ask_text_stream` →
`ResponseAssembler` → `raw_response` pipeline.

**Affects:** step_4.md (test #10).

## D14. `_sum_usage` docstring must state the zero-default contract (round 2)

**Decision:** The `_sum_usage` docstring must explicitly read: "Always returns
all 4 keys (zero-default). Symmetric contract — display layer gates on
`cache_read > 0`." (see D2).

**Rationale:** Without the explicit docstring note, a future maintainer may
"optimize" the helper to drop zero-valued keys, silently breaking the symmetric
contract assumed by consumers.

**Affects:** step_4.md (`_sum_usage` algorithm block).

## D15. Claude CLI regression test asserts round-trip through mapper (round 2)

**Decision:** Rewrite `test_stream_llm_claude_cli_done_event_cache_regression`
(step 3, test #4) to construct a realistic Claude CLI `StreamMessage`
(`{"type": "result", "usage": {"input_tokens": 1200, "output_tokens": 800,
"cache_read_input_tokens": 540, "cache_creation_input_tokens": 0}}`), pass it
through `_map_stream_message_to_event` to produce the done event, then feed
that event into `AppCore.stream_llm()` via a FakeLLMService. Assert
`TokenUsage.input_tokens == 1200`, `output_tokens == 800`,
`cache_read_input_tokens == 540`.

**Rationale:** Asserting only `cache_read` leaves the mapper's handling of the
other fields untested in this regression path. Exercising the real mapper
(not just a hand-crafted done event) verifies the full mapper + AppCore
pipeline in one test.

**Affects:** step_3.md (test #4).
