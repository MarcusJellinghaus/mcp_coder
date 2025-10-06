# Project Plan Decisions

This document logs all decisions made during the project plan review discussion.

## Decision 1: Error Handling Strategy (Hybrid Approach)

**Question:** Should venv requirement be strict or graceful?

**Decision:** **C - Hybrid approach**
- `prepare_llm_environment()` raises `RuntimeError` if no venv found (strict)
- Each caller decides whether to enforce or degrade gracefully
- Workflows can be strict, prompt command can be graceful

**Rationale:** Provides flexibility - workflows enforce strict requirement, but prompt command can continue without env vars for backward compatibility.

---

## Decision 2: Parameter Threading

**Question:** Thread `env_vars` through all layers vs. setting in `os.environ`?

**Decision:** **A - Keep parameter threading**
- Thread `env_vars: dict[str, str] | None = None` through all 7+ function layers
- More explicit and testable
- Avoids global state modification

---

## Decision 3: API Provider Updates

**Question:** Update all 4 functions or just 2 core functions?

**Decision:** **A - Update all 4 functions explicitly**
- Update `_create_claude_client()`, `ask_claude_code_api()`, `ask_claude_code_api_detailed()`, `ask_claude_code_api_detailed_sync()`
- More verbose but symmetric with clear contract

---

## Decision 4: Testing Strategy

**Question:** Create 6 new integration tests or extend existing tests?

**Decision:** Replace Step 8 integration tests with:
- **Unit tests with mocking** - Add to existing test files (Steps 1-6)
- **Extend existing integration test** - Add `test_env_vars_propagation()` to `tests/llm/providers/claude/test_claude_integration.py`

**Rationale:** Minimize real Claude Code calls, leverage existing integration test infrastructure.

---

## Decision 5: Integration Test Details

**Question:** Which existing test to extend and how?

**Decision:** Add new test `test_env_vars_propagation` to `test_claude_integration.py`
- Test both CLI and API methods
- Make real Claude Code calls to verify env_vars work end-to-end
- Verify successful execution means env_vars propagated correctly

---

## Decision 6: Path Format in .mcp.json

**Question:** Use forward slashes or backslashes in .mcp.json paths?

**Decision:** **B - Keep backslashes**
- Use `${MCP_CODER_VENV_DIR}\\Scripts\\mcp-code-checker.exe`
- Windows compatibility verified
- Original plan suggested forward slashes, changed to backslashes

---

## Decision 7: Merge Steps 2 & 3

**Question:** Combine CLI and API provider updates into one step?

**Decision:** **B - Keep separate**
- Step 2: Update CLI provider
- Step 3: Update API provider
- Allows focused testing and smaller commits

---

## Decision 8: Reference Projects in .mcp.json

**Question:** Should reference projects use environment variables?

**Decision:** **A - Keep as-is**
- Reference projects remain with `${USERPROFILE}\\Documents\\GitHub\\...`
- They are external to mcp_coder project
- Not part of portability fix scope

---

## Decision 9: Test File Organization

**Question:** Where to place unit tests for env_vars threading?

**Decision:** **B - tests/llm/test_env.py + extend existing test files**
- Create `tests/llm/test_env.py` for new `prepare_llm_environment()` module
- Add unit tests to existing test files for env_vars parameter threading
- No new test/integration/ directory needed

---

## Decision 10: Number of Steps

**Question:** Keep 8 steps or consolidate to 6?

**Decision:** **A - Keep 8 steps**
- Maintain smaller, focused commits
- Easier to review and test incrementally
- No consolidation needed
