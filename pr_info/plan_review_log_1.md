# Plan Review Log — Issue #819

**Issue**: llm: collect token usage across all providers, display in icoder with cache info
**Branch**: 819-llm-collect-token-usage-across-all-providers-display-in-icoder-with-cache-info
**Started**: 2026-04-16


## Round 1 — 2026-04-16

**Findings**:
- Circular-import risk in step 5 (`agent.py` importing from `langchain/__init__.py`) — moderate
- `_sum_usage` drop-zero-keys filter asymmetric with `_extract_usage` — minor
- Missing ZeroDivisionError guard test (`cache_read > 0` with `input_tokens == 0`) — minor
- Streaming chunk tracking not explicit about last-wins behavior — minor
- Agent test construction risk using `Mock` instead of real `AIMessage` — minor
- Stale line-number references in step 3 — minor
- No Claude CLI regression test for cache flow — minor
- Helper signatures use `dict[str, int]` instead of `UsageInfo` TypedDict — minor
- `cache_creation_input_tokens` flow not explicitly documented — minor
- Observation: no new dependencies; step sizing well-balanced; snapshot tests not affected

**Decisions**:
- Accept all findings autonomously (no user escalation needed — all within existing scope/decisions)
- Q1 helper location → option A: new `_usage.py` submodule (clean separation, avoids circular import)
- Q2 `_sum_usage` semantics → option B: always include all 4 keys (symmetric, simpler)
- Q3 snapshot tests → option B: don't pre-emptively regenerate (investigate during implementation)
- Q4 Claude CLI regression test → option A: add to step 3 (cheap regression guard)

**User decisions**: None (all findings handled autonomously)

**Changes**:
- `summary.md` — documented `_usage.py` location, `cache_creation_input_tokens` flow
- `step_2.md` — added ZeroDivisionError guard test (test #7)
- `step_3.md` — symbolic refs instead of line numbers; added Claude CLI cache regression test (test #4)
- `step_4.md` — new `_usage.py` file; `_sum_usage` returns all 4 keys; `UsageInfo` type; last-wins chunk tracking + test
- `step_5.md` — import from `._usage` submodule; `UsageInfo` for `accumulated_usage`; real `AIMessage` requirement
- `Decisions.md` — new file logging D1-D9

**Status**: applied, pending commit

## Round 2 — 2026-04-16

**Findings**:
- Step 4 `_ask_text_stream` patch location (try-block vs error branch) not explicit — minor
- Step 5 `run_agent_stream` existing done event has no `usage` key — minor (clarity)
- Step 4 test #2 `test_extract_usage_no_metadata` should cover 3 parameterized cases (absent / None / empty) — minor
- Missing `ResponseAssembler` end-to-end test for usage flow to `raw_response` — moderate
- `_sum_usage` needs docstring mandate to prevent future "optimization" back to dropping zeros — minor
- Step 3 test #4 assertion ambiguous — should round-trip through `_map_stream_message_to_event` — minor
- Confirmed: TASK_TRACKER empty is correct per planning principles (populated at impl step 0)
- Confirmed: all round 1 changes applied correctly and internally consistent

**Decisions**: accept all findings autonomously (all refinements within existing scope)

**User decisions**: None

**Changes**:
- `step_3.md` — rewrote test #4 to round-trip through `_map_stream_message_to_event`
- `step_4.md` — pinned patch location to `try:` block; parameterized no-metadata test; added `ResponseAssembler` end-to-end test #10; added `_sum_usage` docstring mandate
- `step_5.md` — clarified existing done event has no `usage` key
- `Decisions.md` — appended D10-D15

**Status**: applied, pending commit

## Round 3 — 2026-04-16

**Findings**:
- All five observations marked `minor` or `none` — informational only, no action needed
- All 15 prior decisions (D1-D15) verified reflected in step files
- All assumptions cross-checked against actual source code (current done-event shapes, try-block structure, `_map_stream_message_to_event` path, `ResponseAssembler` passthrough)
- Step granularity correct, tests mirror-structure correct, parameterization used appropriately

**Decisions**: no changes required

**User decisions**: None

**Changes**: none

**Status**: plan is ready for approval

## Final Status

**Rounds run**: 3
**Plan commits produced**:
- `a24f175` — docs(plan): apply tech-lead review round 1 updates for issue #819
- `4d408d9` — docs(plan): round 2 plan updates for issue #819

**Outcome**: Plan is ready for approval. Three review rounds converged cleanly; all findings were autonomously resolved within existing scope/decisions (no user escalation required). Round 3 produced zero plan changes, confirming stability. The plan now has 15 documented decisions (D1-D15), tests for every new helper and edge case (ZeroDivisionError guard, streaming last-wins middle chunk, `ResponseAssembler` end-to-end usage flow, Claude CLI mapper round-trip regression), and a clean architecture with `_usage.py` as a dedicated submodule avoiding circular imports.
