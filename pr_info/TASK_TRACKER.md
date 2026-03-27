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

### Step 1: Extend ResponseAssembler with tool_trace Accumulation
See [step_1.md](./steps/step_1.md) for details.

- [x] Implementation: tests (`TestResponseAssemblerToolTrace`) + production code in `ResponseAssembler`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(types): add tool_trace accumulation to ResponseAssembler`

### Step 2: Add `run_agent_stream()` Async Generator
See [step_2.md](./steps/step_2.md) for details.

- [x] Implementation: tests (`TestRunAgentStream`) + `run_agent_stream()` in `agent.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(agent): add run_agent_stream async generator with astream_events`

### Step 3: Replace Agent Fallback with Thread+Queue Bridge
See [step_3.md](./steps/step_3.md) for details.

- [ ] Implementation: tests (`TestAskLangchainStreamAgentReal`, `TestAskLangchainStreamAgentTimeouts`) + `_ask_agent_stream()` in `__init__.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(langchain): replace agent streaming fallback with real streaming`

## Pull Request

- [ ] PR review: all steps completed, all checks green
- [ ] PR summary prepared
