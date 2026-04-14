# Plan Review Log — Issue #741

**Issue:** iCoder `/info` slash command + persistent MCPManager
**Reviewer:** Supervisor agent
**Date:** 2026-04-14

## Round 1 — 2026-04-14
**Findings**:
- [C1] Step 1: `_server_names` initialization not documented — unclear how `status()` reports servers before connection
- [C4] Step 2: Ambiguous test file reference — "test_langchain_agent.py (or test_langchain_agent_streaming.py)"
- [R2] Step 1: `close()` algorithm vague about MultiServerMCPClient cleanup
- [M2] Step 4: Unspecified behavior when `mcp_manager=None` — omit section or show placeholder?
- [M6] Step 4: Missing test for `parse_claude_mcp_list` returning None
- Skipped 12 findings as cosmetic, speculative, or implementation details (C2, C3, R1, R3-R6, M1, M3-M5, M7)

**Decisions**:
- C1: Accept — clarify `_server_names = list(server_config.keys())` in `__init__`
- C4: Accept — pin to `test_langchain_agent_streaming.py`
- R2: Accept — explicit `client.__aexit__()` before loop stop
- M2: Accept — omit langchain MCP section entirely when None
- M6: Accept — add test #18 for graceful handling

**User decisions**: None needed — all straightforward improvements
**Changes**: Updated step_1.md (init, close), step_2.md (test file), step_4.md (None behavior, new test)
**Status**: Committed (590a64d)

## Round 2 — 2026-04-14
**Findings**:
- [F1] Step 4: Algorithm missing defensive check for `parse_claude_mcp_list()` returning None — inconsistent with test #18
- [F2] Step 3: Vague test file references — skipped, adequate for plan level
- [F3] Step 1: `client.__aexit__()` correctness — skipped, implementation detail

**Decisions**:
- F1: Accept — added Claude MCP section handling with None guard to _format_info() algorithm
- F2: Skip — LLM will find correct test files during implementation
- F3: Skip — implementation detail

**User decisions**: None needed
**Changes**: Updated step_4.md algorithm to handle parse_claude_mcp_list() returning None
**Status**: Pending commit

