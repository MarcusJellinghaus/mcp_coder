# Plan Review Log — Issue #639

Review of implementation plan for `verify --list-mcp-tools`.

## Round 1 — 2026-03-30

**Findings**:
- (Critical) `--list-mcp-tools` should skip LLM invocation — plan doesn't implement early-return path
- (Critical) `max()` on empty iterable will crash when all servers fail — needs `default=0`
- (Critical) Step 2 must set `.description = None` on existing mock helpers to avoid MagicMock auto-attributes
- (Accept) 3-step decomposition is well-sized
- (Accept) Data flow change (str → tuple) is contained and correct
- (Accept) Test coverage is comprehensive
- (Accept) Output format matches issue requirements
- (Accept) No unnecessary abstractions (YAGNI)
- (Skip) No parameterized tests — not needed here

**Decisions**:
- LLM skip: **ask user** — issue title vs body are contradictory
- `max()` guard: **accept** — straightforward bug fix
- Mock `.description`: **accept** — straightforward test fix

**User decisions**:
- Q: Should `--list-mcp-tools` skip LLM invocation or just change MCP output format?
- A: Option A — full verify still runs, flag only changes MCP output format. The "without invoking LLM" in the title means the tool enumeration itself doesn't need an LLM.

**Changes**:
- `step_2.md`: Added item 4 — `_make_tools_response(count)` must set `.description = None` on mocks
- `step_3.md`: Updated `max()` to use `default=0`; added `test_list_mcp_tools_all_servers_failed` test
- `Decisions.md`: Created with three decisions logged

**Status**: Committed (15c9e95)

## Final Status

- **Rounds**: 1
- **Commits**: 1 (15c9e95 — plan review fixes)
- **Plan status**: Ready for approval. Three issues found and fixed; one design question resolved with user (option A — full verify still runs).
