# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Step 1: Create Environment Variable Preparation Module
- [x] Implement `src/mcp_coder/llm/env.py` with `prepare_llm_environment()` function
- [x] Create `tests/llm/test_env.py` with 4 test cases
- [x] Run pylint, pytest, mypy - fix all issues
- [x] Prepare git commit message for Step 1

**Details:** [pr_info/steps/step_1.md](./steps/step_1.md)

### Step 2: Update CLI Provider with Environment Variables
- [x] Add `env_vars` parameter to `ask_claude_code_cli()` in `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- [x] Update tests in `tests/llm/providers/claude/test_claude_code_cli.py`
- [x] Run pylint, pytest, mypy - fix all issues
- [x] Prepare git commit message for Step 2

**Details:** [pr_info/steps/step_2.md](./steps/step_2.md)

### Step 3: Update API Provider with Environment Variables
- [ ] Add `env_vars` parameter to 4 functions in `src/mcp_coder/llm/providers/claude/claude_code_api.py`
- [ ] Update tests in `tests/llm/providers/claude/test_claude_code_api.py`
- [ ] Run pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 3

**Details:** [pr_info/steps/step_3.md](./steps/step_3.md)

### Step 4: Update Interface Layer with Environment Variables
- [ ] Add `env_vars` parameter to `ask_llm()` and `prompt_llm()` in `src/mcp_coder/llm/interface.py`
- [ ] Add `env_vars` parameter to `ask_claude_code()` in `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
- [ ] Update tests in `tests/llm/test_interface.py` and `tests/llm/providers/claude/test_claude_code_interface.py`
- [ ] Run pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 4

**Details:** [pr_info/steps/step_4.md](./steps/step_4.md)

### Step 5: Update Workflows with Environment Preparation
- [ ] Add environment preparation to `prepare_task_tracker()` in `src/mcp_coder/workflows/implement/core.py`
- [ ] Add environment preparation to `generate_commit_message_with_llm()` in `src/mcp_coder/utils/commit_operations.py`
- [ ] Update tests in `tests/workflows/implement/test_core.py` and `tests/utils/test_commit_operations.py`
- [ ] Run pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 5

**Details:** [pr_info/steps/step_5.md](./steps/step_5.md)

### Step 6: Update CLI Commands (Minimal Changes)
- [ ] Add environment preparation to `execute_prompt()` in `src/mcp_coder/cli/commands/prompt.py`
- [ ] Update tests in `tests/cli/commands/test_prompt.py`
- [ ] Run pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 6

**Details:** [pr_info/steps/step_6.md](./steps/step_6.md)

### Step 7: Update .mcp.json Template
- [ ] Replace hardcoded paths with `${MCP_CODER_PROJECT_DIR}` and `${MCP_CODER_VENV_DIR}` in `.mcp.json`
- [ ] Manual testing: Verify MCP servers work with environment variables
- [ ] Prepare git commit message for Step 7

**Details:** [pr_info/steps/step_7.md](./steps/step_7.md)

### Step 8: Integration Testing
- [ ] Add integration test `test_env_vars_propagation()` in `tests/llm/providers/claude/test_claude_integration.py`
- [ ] Run full test suite (all unit tests + integration test)
- [ ] Run pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 8

**Details:** [pr_info/steps/step_8.md](./steps/step_8.md)

---

## Pull Request

### Final Review and Submission
- [ ] Review all changes across all 8 steps
- [ ] Verify all tests pass (unit + integration)
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Create pull request with summary of all changes
- [ ] Verify PR description includes testing strategy and manual verification steps

**Summary:** [pr_info/steps/summary.md](./steps/summary.md)
