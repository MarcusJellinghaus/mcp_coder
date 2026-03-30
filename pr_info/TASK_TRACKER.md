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

### Step 1: Dependencies + Package Skeleton + Types
> [step_1.md](./steps/step_1.md) — Add Textual dependencies, create icoder package skeleton, implement core type definitions (Response, Command, EventEntry)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Event Log
> [step_2.md](./steps/step_2.md) — Implement structured event log with in-memory list + JSONL file output (EventLog class with context manager)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Command Registry + Built-in Commands
> [step_3.md](./steps/step_3.md) — Implement slash command registry with decorator-based registration and /help, /clear, /quit commands

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: LLM Service Protocol
> [step_4.md](./steps/step_4.md) — Create LLMService Protocol, RealLLMService wrapping prompt_llm_stream(), and FakeLLMService for testing

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: AppCore — Central Input Routing
> [step_5.md](./steps/step_5.md) — Implement AppCore coordinator that routes input to commands or LLM, manages session state, emits events

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: CLI Wiring
> [step_6.md](./steps/step_6.md) — Register `mcp-coder icoder` CLI command with standard flags, wire parser and routing in main.py

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: UI Widgets (styles, OutputLog, InputArea)
> [step_7.md](./steps/step_7.md) — Implement Textual UI widgets: CSS styles, OutputLog(RichLog), InputArea(TextArea) with Enter=submit

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: ICoderApp + Pilot Integration Tests
> [step_8.md](./steps/step_8.md) — Implement ICoderApp wiring UI events to AppCore, async LLM bridging, Textual pilot tests

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Snapshot Tests (SVG Visual Regression)
> [step_9.md](./steps/step_9.md) — Add pytest-textual-snapshot dependency and Windows-only SVG snapshot tests

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review completed
- [ ] PR summary prepared
