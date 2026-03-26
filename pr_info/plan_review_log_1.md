# Plan Review Log — Issue #603

**Issue:** feat(langchain): add real streaming for LangChain agent mode
**Branch:** 603-feat-langchain-add-real-streaming-for-langchain-agent-mode
**Reviewer:** Supervisor agent

## Round 1 — 2026-03-27

**Findings:**
- (Critical) `tool_call_id` sourced from `run_id` is semantically wrong — `run_id` is a LangChain internal UUID, not the LLM's tool_call_id
- (Critical) `tool_call_id` not available in `on_tool_start` events — only in `on_tool_end` via `ToolMessage.tool_call_id`
- (Critical) `BaseException` catch should be `Exception` to avoid catching `KeyboardInterrupt`/`SystemExit`
- (Accept) History serialization from stream events unspecified — needs accumulation strategy
- (Accept) `AIMessageChunk` mock approach needs clarification in step 2
- (Accept) Old blocking path tests unaffected — should be noted
- (Accept) No `langchain_integration` marker confirmation needed for new unit tests
- (Accept) `GeneratorExit` + `error_holder` re-raise ordering could mask GeneratorExit
- (Skip) Missing empty content filter test — cosmetic
- (Skip) Prescriptive commit messages — cosmetic
- (Skip) Redundant `@pytest.mark.asyncio` decorators — cosmetic

**Decisions:**
- Critical 1&2: Fixed — use `run_id` for correlation, extract real `tool_call_id` from `ToolMessage` on `on_tool_end`, added explanatory note
- Critical 3: Fixed — changed `BaseException` to `Exception`
- Accept (history): User chose Option A — accumulate from stream events. Added HISTORY ACCUMULATION section to step 2
- Accept (AIMessageChunk mock): Added note — tests mock at `astream_events` level, no conftest changes needed
- Accept (blocking path): Added note to step 3 that `ask_langchain()` and `_ask_agent()` are unchanged
- Accept (markers): Added note — new tests are unit tests, no `langchain_integration` marker
- Accept (GeneratorExit): Added `cancelled` flag to prevent error re-raise after GeneratorExit
- Skip items: Not actioned

**User decisions:**
- History storage approach: Option A (accumulate from stream events) — approved by user
- Issue scope: User confirmed proceeding with current 4-step plan, no split needed

**Changes:**
- `pr_info/steps/step_2.md`: tool_call_id fix, history accumulation section, mock notes, marker note
- `pr_info/steps/step_3.md`: BaseException→Exception, blocking path note, GeneratorExit flag fix

**Status:** Ready to commit

## Final Status

Plan review complete. 1 round, 3 critical fixes + 5 accept improvements applied. Plan is ready for approval.
