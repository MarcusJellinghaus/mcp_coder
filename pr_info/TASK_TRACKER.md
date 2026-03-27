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

- [x] Implementation: tests (`TestAskLangchainStreamAgentReal`, `TestAskLangchainStreamAgentTimeouts`) + `_ask_agent_stream()` in `__init__.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(langchain): replace agent streaming fallback with real streaming`

## LLM testing during code review

- [x] Claude CLI streaming: `mcp-coder prompt --llm-method claude --output-format ndjson "Count from 1 to 5"` — works, returns text + result events
- [x] LangChain text streaming (no MCP): `mcp-coder prompt --llm-method langchain --output-format ndjson "Count from 1 to 5"` — works after fixing pre-existing `http_client` bug in `anthropic_backend.py`
- [x] LangChain agent streaming — MCP server visibility: can LLM list available tools?
- [x] LangChain agent streaming — list directory via MCP workspace tools
- [x] LangChain agent streaming — file lifecycle: create, read, edit, delete file via MCP

Batch file: `tools/manual_streaming_tests.bat` (run from project root)

## Open Issues

- [x] `--output-format text` streams correctly for all providers (verified with timestamp diagnostic)
- [ ] `--output-format ndjson` batches text_delta events into single `assistant` messages for Claude CLI and LangChain text mode — pre-existing formatter issue, not caused by this PR
- [x] Agent mode `--mcp-config` works when `VIRTUAL_ENV` is set (batch file now activates venv)
- [ ] Misleading error message when `VIRTUAL_ENV` not set: shows "Connection to Anthropic API failed" instead of MCP subprocess not found

Diagnostic: `tools/streaming_diagnostic.py` (run with `.venv/Scripts/python tools/streaming_diagnostic.py`)
- [ ] decide what should happen with `tools\manual_streaming_tests.bat`

## Pull Request

- [x] PR review: all steps completed, all checks green
- [ ] PR summary prepared
