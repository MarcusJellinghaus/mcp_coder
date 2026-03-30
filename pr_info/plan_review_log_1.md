# Plan Review Log #1 — Issue #617

**Issue**: iCoder - initial setup: Textual TUI with three-layer architecture
**Date**: 2026-03-30
**Reviewer**: Automated plan review (supervisor + engineer subagent)

---

## Round 1 — 2026-03-30

**Findings**:
- (CRITICAL) Step 1: `textual` added as main dependency — bloats all installations; should be optional
- (CRITICAL) Step 2: EventLog opens file handle in constructor without context manager — file handle leak risk
- (CRITICAL) Step 4: RealLLMService has no delegation test — only structural `hasattr` check
- (CRITICAL) Step 6: References non-existent `find_latest_session_id()` — actual API is two-step
- (CRITICAL) Step 7: Too large for single commit — 5 source files + test file + async bridging
- (CRITICAL) Step 7: Pilot test assertions are comment placeholders, not real assertions
- (CRITICAL) Step 1: `pytest-textual-snapshot` added too early — only used in step 8
- (ACCEPT) Steps 2, 3, 5: Well-designed, good test coverage, no issues
- (ACCEPT) Step 4: Protocol-based DI is the right choice; FakeLLMService in source is good
- (ACCEPT) Summary architecture: Three-layer design is sound
- (SKIP) Step 8 snapshot tests: Fragility concern noted but kept — explicitly in issue scope

**Decisions**:
- Accept all 7 critical findings — all are straightforward improvements, no design/scope questions
- Skip deferring snapshot tests — they are in issue scope

**User decisions**: None needed — all findings were straightforward

**Changes**:
- step_1.md: textual → optional `tui` extras group; removed pytest-textual-snapshot (deferred to step 9)
- step_2.md: Added EventLog `__enter__`/`__exit__` + context manager test
- step_4.md: Added RealLLMService delegation test with patched `prompt_llm_stream`
- step_5.md: Updated conftest fixture to use EventLog context manager
- step_6.md: Fixed to two-step session API; EventLog as context manager; lazy textual import note
- step_7.md: Rewritten — widgets only (styles.py, output_log.py, input_area.py) + widget tests
- step_8.md: New — ICoderApp + async bridging + pilot tests with concrete assertions
- step_9.md: New — former step 8 (snapshot tests) renumbered; pytest-textual-snapshot added here
- summary.md: Updated to 9 steps with all changes reflected
- Decisions.md: Created with all 7 review decisions documented

**Status**: Committing changes

