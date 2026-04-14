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

### Step 1: MCPManager — Persistent MCP Client
> [Detail](./steps/step_1.md) — Create `MCPManager` class in `src/mcp_coder/llm/mcp_manager.py`

- [x] Implementation: `MCPManager` class + tests in `tests/llm/test_mcp_manager.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `run_agent_stream()` Accepts Optional Pre-built Tools
> [Detail](./steps/step_2.md) — Add optional `tools` parameter to `run_agent_stream()`

- [x] Implementation: modify `agent.py` + tests in `test_langchain_agent_streaming.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3A: Thread `tools` Through `_ask_agent_stream()` and `ask_langchain_stream()`
> [Detail](./steps/step_3.md) — Add `tools` param to langchain provider functions

- [x] Implementation: modify `langchain/__init__.py` + tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3B: Thread `tools` Through `prompt_llm_stream()`
> [Detail](./steps/step_3.md) — Add `tools` param to LLM interface

- [x] Implementation: modify `interface.py` + tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3C: Add `mcp_manager` to `RealLLMService`
> [Detail](./steps/step_3.md) — Add `mcp_manager` parameter to `RealLLMService`

- [ ] Implementation: modify `llm_service.py` + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `/info` Command
> [Detail](./steps/step_4.md) — Create `/info` slash command in `src/mcp_coder/icoder/core/commands/info.py`

- [ ] Implementation: `/info` command + `_redact_env_vars` + tests in `tests/icoder/test_info_command.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Wire Everything in `execute_icoder()`
> [Detail](./steps/step_5.md) — Wire `MCPManager`, `/info`, and cleanup in `icoder.py`

- [ ] Implementation: modify `execute_icoder()` + tests in `tests/icoder/test_cli_icoder.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
