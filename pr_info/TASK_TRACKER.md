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

### Step 1: Add `reset_session` field to `Response` dataclass
- [x] Implementation: add `reset_session: bool = False` to `Response` + tests in `test_types.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(icoder): add reset_session flag to Response dataclass`

### Step 2: Add `reset_session()` to `LLMService` protocol + implementations
- [x] Implementation: add `reset_session()` to protocol, `RealLLMService`, `FakeLLMService` + tests in `test_llm_service.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(icoder): add reset_session() to LLMService protocol`

### Step 3: Wire `/clear` → session reset in AppCore
- [x] Implementation: update `/clear` handler to set `reset_session=True`, update `AppCore.handle_input()` to act on flag + tests in `test_app_core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(icoder): /clear resets LLM session (#765)`

### Step 4: Fresh session by default + `--continue-session` flag
- [x] Implementation: add session continuation args to icoder parser, replace auto-resume with opt-in continuation + tests in `test_parsers.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(icoder): fresh session by default, add --continue-session flag (#765)`

### Step 5: Auto-store iCoder sessions for Claude provider
- [ ] Implementation: add `provider` property to `LLMService` protocol + implementations, update `AppCore.stream_llm()` to auto-store responses + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(icoder): auto-store sessions for --continue-session support (#765)`

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
