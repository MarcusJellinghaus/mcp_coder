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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1 — Project Configuration ([step_1.md](./steps/step_1.md))

- [x] Implement Step 1: add `langchain` optional extra, pytest marker, mypy overrides to `pyproject.toml`; add `langchain_library_isolation` contract to `.importlinter`
- [x] Run quality checks (pylint, mypy) and fix all issues found
- [x] Prepare git commit message

---

### Step 2 — Session History Storage ([step_2.md](./steps/step_2.md))

- [x] Implement Step 2 (TDD): write tests in `tests/llm/storage/test_session_storage.py`, then add `store_langchain_history()`, `load_langchain_history()`, `_langchain_session_path()` to `src/mcp_coder/llm/storage/session_storage.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [x] Prepare git commit message

---

### Step 3 — LangChain Provider Package ([step_3.md](./steps/step_3.md))

- [x] Implement Step 3 (TDD): create test files under `tests/llm/providers/langchain/`, then create provider source files (`__init__.py`, `openai.py`, `gemini.py`, `_utils.py`); update `tests/llm/providers/test_provider_structure.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [x] Prepare git commit message

---

### Step 3b — LangChain Integration Tests ([step_3b.md](./steps/step_3b.md))

- [x] Implement Step 3b: create `tests/llm/providers/langchain/test_langchain_integration.py` with skip-helper and two integration tests marked `langchain_integration`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [x] Prepare git commit message

---

### Step 4 — Interface Routing ([step_4.md](./steps/step_4.md))

- [x] Implement Step 4 (TDD): append `TestPromptLlmLangchainRouting` to `tests/llm/test_interface.py`, then add `MCP_CODER_LLM_PROVIDER` env var override and `if provider == "langchain":` branch to `src/mcp_coder/llm/interface.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [x] Prepare git commit message

---

### Step 5 — Documentation ([step_5.md](./steps/step_5.md))

- [x] Implement Step 5: add `[llm]` / `[llm.langchain]` section to `docs/configuration/config.md`; update LLM provider section and session storage description in `docs/architecture/architecture.md`
- [x] Run quality checks (pylint, mypy) and fix all issues found
- [x] Prepare git commit message

---

## Pull Request

- [ ] Review all changes across steps 1–5 for consistency and completeness
- [ ] Confirm all tests pass (`pytest`) with no regressions
- [ ] Write PR summary (title, description, test plan)
