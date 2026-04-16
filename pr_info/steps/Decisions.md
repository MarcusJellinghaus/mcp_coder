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
