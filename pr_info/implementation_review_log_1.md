# Implementation Review Log — Issue #819

Token usage collection across all providers, with iCoder cache display.

## Round 1 — 2026-04-16

**Findings**:
- Critical: none.
- Accept (Boy-Scout, optional):
  1. `_extract_usage` docstring says "Returns {} if no usage data is available" but the helper actually returns a partial `UsageInfo` containing only keys present in metadata. Minor imprecision.
  2. `_ask_text_stream` local `last_chunk_with_usage` is `Any`-typed; `AIMessageChunk | None` would be more precise.
  3. `icoder/core/types.py` `display_text()` uses escaped `\u2193/\u2191` rather than literal arrows.
- Skip (speculative / pre-existing):
  - mypy "Statement is unreachable" at `src/mcp_coder/utils/tui_preparation.py:121` — pre-existing, file untouched by this branch.
  - `store_langchain_history` in `_ask_text_stream` still stores the AI message without extracted `usage_metadata` — pre-existing behavior, out of scope.
  - 404/model-not-found handler duplicated between `_ask_text` and `_ask_text_stream` — pre-existing duplication, out of scope.

**Decisions**:
- All three Accept items → **Skip**. Reason: purely cosmetic. Per `software_engineering_principles.md` ("Don't change working code for cosmetic reasons when it's already readable") and the "Skip" bucket definition (speculative/cosmetic). None has behavioral impact; all tests pass.
- All Skip items stay skipped — pre-existing and unrelated to issue #819.

**Plan compliance** (all 15 decisions D1–D15 verified against `pr_info/steps/Decisions.md`):
- D1 `_usage.py` submodule exists; imported by both `__init__.py` and `agent.py` (no circular import).
- D2/D14 `_sum_usage` returns all 4 keys with zero default; docstring explicitly states the contract.
- D3 Both helpers typed as `UsageInfo`.
- D4 `display_text()` guards against `ZeroDivisionError` (test covers `update(0, 0, 100)`).
- D5 Last-wins tracking via `last_chunk_with_usage`; middle-chunk regression test present.
- D6 Agent tests use real `AIMessage` instances (via conftest).
- D8/D15 Claude CLI round-trip regression test exercises mapper + AppCore pipeline with all 3 fields.
- D9 `cache_creation_input_tokens` flows through `raw_response["usage"]` but is not displayed.
- D10 Stream patch confined to the success `try:` block; error/timeout branches unchanged.
- D11 `run_agent_stream` done event now carries `"usage"` key.
- D12 `test_extract_usage_no_metadata` parameterized over attr-absent / `None` / empty-dict.
- D13 `test_ask_text_stream_usage_flows_to_raw_response` exercises all 4 fields through `ResponseAssembler`.

**Quality checks**:
- pylint: PASS
- pytest (3660 unit tests): PASS
- mypy: PASS on branch files (one pre-existing error in unrelated `tui_preparation.py`).
- ruff: PASS

**Changes**: none — all findings triaged as Skip.

**Status**: no changes needed.

## Final Status

Single review round produced zero code changes. All plan decisions (D1–D15) are implemented; all quality checks pass on files modified by this branch. No critical or accept-bucket blockers. Implementation is ready for PR review / merge.
