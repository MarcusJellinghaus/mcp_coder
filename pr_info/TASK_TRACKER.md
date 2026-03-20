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

### Step 1 — Dependencies + Agent Utilities ([step_1.md](./steps/step_1.md))
- [x] Implement Step 1: add dependencies to pyproject.toml, create agent.py with `_resolve_env_vars` and `_load_mcp_server_config`, update conftest.py mocks, write tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 1

### Step 2 — Agent Execution Core ([step_2.md](./steps/step_2.md))
- [x] Implement Step 2: add `run_agent()` async function to agent.py with MultiServerMCPClient + create_react_agent, write tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 2

### Step 3a — Backend Refactor + Chat Model Helper ([step_3a.md](./steps/step_3a.md))
- [x] Implement Step 3a: extract `create_*_model()` from each backend, add `_create_chat_model()` dispatcher in __init__.py, add `_check_agent_dependencies()` to agent.py, write tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 3a

### Step 3b — Agent Mode Routing + Session + MLflow ([step_3b.md](./steps/step_3b.md))
- [x] Implement Step 3b: extend `ask_langchain()` with mcp_config/execution_dir/env_vars params, add agent mode routing via asyncio.run, widen session type hints, write tests
- [x] Implement MLflow logging sub-commit for agent mode (params, metrics, tool_trace.json artifact)
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 3b

### Step 4 — Update interface.py Routing ([step_4.md](./steps/step_4.md))
- [x] Implement Step 4: pass mcp_config, execution_dir, env_vars through to `ask_langchain()` in `prompt_llm()`, write tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 4

### Step 5 — Verification Extensions ([step_5.md](./steps/step_5.md))
- [x] Implement Step 5: add `_check_mcp_adapter_packages()` to verification.py, extend `verify_langchain()` with MCP checks and end-to-end agent test, add `--mcp-config` to parsers.py, update label map in verify.py, write tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 5

### Step 6 — Code Review Fixes: Small Cleanups ([step_6.md](./steps/step_6.md))
- [x] Implement Step 6: remove dead transport branch in agent.py, add TYPE_CHECKING guard for BaseChatModel in __init__.py, wire env_vars through in verification.py, add _check_agent_dependencies tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 6

### Step 7 — Unify Text Backend via `_create_chat_model` ([step_7.md](./steps/step_7.md))
- [x] Implement Step 7: rewrite _ask_text() to use _create_chat_model() + generic .invoke(), delete old ask_openai/ask_gemini/ask_anthropic functions, update all affected tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 7

### Step 8 — Quick Fixes: Imports, Docstrings, Dead Code, SecretStr ([step_8.md](./steps/step_8.md))
- [x] Implement Step 8: add `from __future__ import annotations` to gemini_backend.py and _utils.py, fix stale _utils.py docstring, remove unused `_ai_message_to_dict`, wrap Gemini API key in SecretStr, add TYPE_CHECKING guard for BaseChatModel in agent.py, convert agent.py docstrings to Google-style
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 8

### Step 9 — Timeout Propagation + asyncio.TimeoutError Handling ([step_9.md](./steps/step_9.md))
- [x] Implement Step 9: pass timeout through _create_chat_model() to backend factories, add asyncio.TimeoutError handler in prompt_llm(), write tests
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 9

### Step 10 — Unify Session History Format ([step_10.md](./steps/step_10.md))
- [ ] Implement Step 10: change _ask_text() to use model_dump() / messages_from_dict() for history serialization, remove _to_lc_messages() if unused, update tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 10

### Step 11 — Config Robustness + Transport Warning ([step_11.md](./steps/step_11.md))
- [ ] Implement Step 11: wrap json.JSONDecodeError in _load_mcp_server_config() with user-friendly message, log warning when overriding non-stdio transport, write tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 11

### Step 12 — Test Coverage Gaps ([step_12.md](./steps/step_12.md))
- [ ] Implement Step 12: add tests for empty message list, non-dict server entry skipping, execution_dir/env_vars forwarding, ImportError for all three backends
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 12

## Pull Request
- [ ] Review all changes across steps for consistency and completeness
- [ ] Run full quality checks suite (pylint, pytest, mypy) on entire changeset
- [ ] Prepare PR title and summary describing the MCP tool-use support feature
