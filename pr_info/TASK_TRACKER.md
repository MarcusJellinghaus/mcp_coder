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

### Step 1: Pure filter function `filter_tools_by_declaration`

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: `tests/llm/test_skill_tool_filter.py` (new) + module-level `filter_tools_by_declaration` in `mcp_manager.py` (TDD, not wired to any caller)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `MCPManager` canonical-name stamping + accessor

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation: `canonical_name()` accessor + `mcp__{server}__{tool}` stamp in `_connect_and_discover`; tests in `tests/llm/test_mcp_manager.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `SendToLLM.allowed_tools` field + skill handler populates it

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation: add `allowed_tools` field to `SendToLLM` (`types.py`) + populate in `_make_langchain_handler` (`skills.py`); tests in `test_types.py`, `test_skills.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Service layer — enforcement toggle, `stream(allowed_tools=…)`, filtering + warning

Detail: [step_4.md](./steps/step_4.md)

- [ ] Implementation: widen `stream()` on Protocol/`RealLLMService`/`FakeLLMService`; `enforce_skill_tools` ctor arg; filtering + `permission_warning` yield; tests in `test_llm_service.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: End-to-end threading — `AppCore`, `ui/app.py`, CLI wiring

Detail: [step_5.md](./steps/step_5.md)

- [ ] Implementation: preserve field in `handle_input` (`replace`); `stream_llm` forwards; UI worker threads field; `permission_warning` render guard; CLI passes `enforce_skill_tools=False`; tests in `test_app_core.py`, `test_app_pilot.py`, `test_cli_icoder.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: address review feedback
- [ ] PR summary prepared
