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

### Step 1: Extend `MLflowLogger` with LRU Session Map ([step_1.md](./steps/step_1.md))

- [x] Implement `TestSessionMapBehavior` (6 tests) in `tests/llm/test_mlflow_logger.py` — write tests first (TDD)
- [x] Implement LRU session map changes in `src/mcp_coder/llm/mlflow_logger.py`: `OrderedDict` import, `_MAX_SESSION_MAP_SIZE`, `_session_run_map`, `has_session()`, `log_conversation_artifacts()`, extend `start_run()` and `end_run()`
- [x] Run quality checks (pylint, pytest, mypy) and resolve all issues found
- [x] Prepare git commit message for Step 1 changes

### Step 2: Add `session_id` to `log_llm_response()` and Call `end_run()` ([step_2.md](./steps/step_2.md))

- [x] Add 3 new tests to `TestLogLLMResponse` in `tests/llm/providers/claude/test_logging_utils.py` — write tests first (TDD)
- [ ] Modify `log_llm_response()` in `src/mcp_coder/llm/providers/claude/logging_utils.py`: add `session_id` parameter and call `mlflow_logger.end_run("FINISHED", session_id=session_id)` at end; remove stale comment
- [ ] Run quality checks (pylint, pytest, mypy) and resolve all issues found
- [ ] Prepare git commit message for Step 2 changes

### Step 3: Thread `session_id` Through CLI and API Callers ([step_3.md](./steps/step_3.md))

- [ ] Add test to `tests/llm/providers/claude/test_claude_code_cli.py` verifying `session_id` is passed to `log_llm_response()` — write test first (TDD)
- [ ] Add test to `tests/llm/providers/claude/test_claude_code_api.py` verifying `session_id` is passed to `log_llm_response()` — write test first (TDD)
- [ ] Pass `session_id=parsed["session_id"]` to `log_llm_response()` in `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- [ ] Pass `session_id=actual_session_id` to `log_llm_response()` in `src/mcp_coder/llm/providers/claude/claude_code_api.py`
- [ ] Run quality checks (pylint, pytest, mypy) and resolve all issues found
- [ ] Prepare git commit message for Step 3 changes

### Step 4: Update `_log_to_mlflow()` in `prompt.py` ([step_4.md](./steps/step_4.md))

- [ ] Add `TestLogToMlflow` class (5 tests) to `tests/cli/commands/test_prompt.py` — write tests first (TDD)
- [ ] Rewrite `_log_to_mlflow()` in `src/mcp_coder/cli/commands/prompt.py`: extract `response_sid`, add conditional resume-run vs fresh-run branches, remove standalone `end_run()` call
- [ ] Run quality checks (pylint, pytest, mypy) and resolve all issues found
- [ ] Prepare git commit message for Step 4 changes

---

## Pull Request

- [ ] Review all changes across the 4 steps for correctness and consistency with [summary.md](./steps/summary.md) and [Decisions.md](./steps/Decisions.md)
- [ ] Verify full test suite passes (all existing tests + all new tests)
- [ ] Write PR title and summary describing the fix for issue #491 "Fix MLflow 'already active run' warning"
