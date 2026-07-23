# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Lazy named thread target in `_ask_agent_stream` (production)

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation — replace eager `Thread(target=asyncio.run, args=(_run(),))` with named `_thread_main()` closure and `target=_thread_main` in `src/mcp_coder/llm/providers/langchain/__init__.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Repoint non-stream error-path patches to `run_agent` (test-only)

Detail: [step_2.md](./steps/step_2.md)

- [ ] Implementation — add `AsyncMock` import; repoint the 3 error-path tests to `{_MOD}.agent.run_agent` with `new_callable=AsyncMock` in `tests/llm/providers/langchain/test_langchain_provider.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Repoint + strengthen `test_agent_mode_passes_system_messages` (test-only)

Detail: [step_3.md](./steps/step_3.md)

- [ ] Implementation — add `AsyncMock` import; repoint patch to `{_MOD}.agent.run_agent` with `new_callable=AsyncMock`; strengthen assertion to check `system_messages` content in `tests/llm/providers/langchain/test_langchain_provider_system_messages.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Final PR summary and verification (unit subset reports `0 warnings`)
