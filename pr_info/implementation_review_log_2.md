# Implementation Review Log — Run 2

**Issue:** #603 — feat(langchain): add real streaming for LangChain agent mode
**Date:** 2026-03-27

## Round 1 — 2026-03-27

**Findings:**
- (1) `args` emitted as JSON string in `tool_use_start` events, inconsistent with docstring and non-streaming path
- (2) `timeout` parameter not used for agent-level timeout (already covered in run 1)
- (3) Error event message may not match final raised exception after `_handle_provider_error`
- (4) No test for auth/connection error transformation in `_ask_agent_stream`
- (5) `chunk.content` access could `AttributeError` on unexpected object
- (6) Tool call correlation approach is fine for practical use
- (7) Overall timeout check after yield is benign

**Decisions:**
- (1) **Accept** — Real inconsistency affecting `tool_trace` consumers. Bounded fix.
- (2) **Skip** — Already covered in run 1 as intentional design.
- (3) **Skip** — Not a correctness bug; current behavior is reasonable for consumer pattern.
- (4) **Accept** — Bounded test addition, increases confidence in error path.
- (5) **Skip** — Speculative; `on_chat_model_stream` always yields `AIMessageChunk` with `.content`.
- (6) **Skip** — Fine per reviewer.
- (7) **Skip** — Benign edge case.

**Changes:**
- Changed `run_agent_stream()` to emit `args` as dict instead of JSON string in `tool_use_start` events (`agent.py`)
- Updated `test_tool_use_start_from_on_tool_start` to assert dict args (`test_langchain_agent_streaming.py`)
- Added `TestAskLangchainStreamAgentAuthError` test for auth error transformation (`test_langchain_streaming.py`)

**Status:** Committed as `374288b`

## Round 2 — 2026-03-27

**Findings:** None. Fresh review of all key files found no new issues beyond what was already addressed.

**Decisions:** N/A

**Changes:** None

**Status:** No changes needed

## Final Status

- **Rounds:** 2
- **Commits:** 1 (`374288b` — args type fix + auth error test)
- **Remaining issues:** None blocking
- **Code quality:** All checks pass (pylint, mypy, pytest)
