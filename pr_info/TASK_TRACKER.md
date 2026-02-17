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

### Step 1 – Extend `store_session()` and `extract_session_id()`

See [step_1.md](./steps/step_1.md) for full details.

- [x] Implement Step 1: extend `store_session()` with `step_name`/`branch_name` params and new filename format; add `LLMResponseDict` support; update `extract_session_id()` with new lookup path
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [x] Prepare git commit message for Step 1

### Step 2 – Simplify LLM Interface: `ask_llm()` thin wrapper + centralise `TimeoutExpired` + delete `claude_code_interface.py`

See [step_2.md](./steps/step_2.md) for full details.

- [ ] Implement Step 2: rewrite `ask_llm()` as thin wrapper over `prompt_llm()`; add `TimeoutExpired` handling to `prompt_llm()`; delete `claude_code_interface.py` and its test file; update `test_interface.py` mocks
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 2

### Step 3 – Remove `pr_info/.conversations/` logging infrastructure

See [step_3.md](./steps/step_3.md) for full details.

- [ ] Implement Step 3: delete `save_conversation()`, `save_conversation_comprehensive()`, `_call_llm_with_comprehensive_capture()`; remove `CONVERSATIONS_DIR`; remove `.conversations/` dir creation; replace call sites with `ask_llm()`; update tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 3

### Step 4 – Switch `task_processing.py` to `prompt_llm()` + `store_session()`

See [step_4.md](./steps/step_4.md) for full details.

- [ ] Implement Step 4: replace `ask_llm()` calls in `process_single_task()` and `check_and_fix_mypy()` with `prompt_llm()` + `store_session()`; write sessions to `.mcp-coder/implement_sessions/`; update tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 4

### Step 5 – Switch `core.py` to `prompt_llm()` + `store_session()`

See [step_5.md](./steps/step_5.md) for full details.

- [ ] Implement Step 5: replace all four `ask_llm()` call sites in `core.py` (`_run_ci_analysis`, `_run_ci_fix`, `prepare_task_tracker`, `run_finalisation`) with `prompt_llm()` + `store_session()`; wrap storage in try/except; update tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 5

### Step 6 – Update `create_plan.py` and `prompt.py` to pass `LLMResponseDict` directly to `store_session()`

See [step_6.md](./steps/step_6.md) for full details.

- [ ] Implement Step 6: remove manual dict wrapping in `create_plan.py` (×3 call sites); switch `prompt.py` just-text mode to `prompt_llm()`; switch `prompt.py` verbose/raw mode to `prompt_llm()`; narrow `store_session()` type annotation; simplify model extraction; remove unused imports; update tests
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues found
- [ ] Prepare git commit message for Step 6

---

## Pull Request

- [ ] Review all changes across all steps for correctness and completeness
- [ ] Verify all tests pass and no regressions introduced
- [ ] Write PR summary describing the implement logging improvement (removal of `.conversations/`, addition of structured session JSON to `.mcp-coder/implement_sessions/`)
