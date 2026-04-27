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

### Step 1: Bump `mcp-coder-utils` dependency

See [step_1.md](./steps/step_1.md) for details.

- [x] Implementation (update `mcp-coder-utils` constraint in `pyproject.toml`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Rename misleading test file

See [step_2.md](./steps/step_2.md) for details.

- [x] Implementation (rename `test_claude_cli_stream_integration.py` → `test_claude_cli_stream_logging_integration.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Real-CLI streaming integration tests

See [step_3.md](./steps/step_3.md) for details.

- [x] Implementation (create `test_claude_code_cli_streaming_integration.py` with three integration tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: iCoder `RealLLMService.stream()` smoke test

See [step_4.md](./steps/step_4.md) for details.

- [x] Implementation (append `test_real_llm_service_stream_smoke` to `tests/icoder/test_llm_service.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review completed
- [ ] PR summary prepared
