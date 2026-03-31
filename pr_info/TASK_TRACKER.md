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

### Step 1: Subprocess Inactivity Watchdog Timeout
> [Detail](./steps/step_1.md) — Replace `threading.Timer` with watchdog daemon thread in `stream_subprocess()`

- [ ] Implementation: tests (`tests/utils/test_subprocess_streaming.py`) + production code (`src/mcp_coder/utils/subprocess_streaming.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: inactivity watchdog timeout for stream_subprocess`

### Step 2: LangChain Text Stream Inactivity Timeout
> [Detail](./steps/step_2.md) — Add inactivity timeout between chunks in `_ask_text_stream()`

- [ ] Implementation: tests (`tests/llm/providers/langchain/test_langchain_streaming_timeout.py`) + production code (`src/mcp_coder/llm/providers/langchain/__init__.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: langchain text stream inactivity timeout`

### Step 3: LLM Service Timeout Constant + Agent Timeout Passthrough
> [Detail](./steps/step_3.md) — Define `ICODER_LLM_TIMEOUT_SECONDS = 300`, pass to `prompt_llm_stream()`, replace `_AGENT_NO_PROGRESS_TIMEOUT` with caller's timeout

- [ ] Implementation: tests (`tests/icoder/test_llm_service.py`) + production code (`src/mcp_coder/icoder/services/llm_service.py`, `src/mcp_coder/llm/providers/langchain/__init__.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: 5-minute inactivity timeout for LLM calls`

### Step 4: Batch Files — icoder.bat + icoder_local.bat
> [Detail](./steps/step_4.md) — Create Windows launchers following `claude.bat` / `claude_local.bat` pattern

- [ ] Implementation: create `icoder.bat` and `icoder_local.bat`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: add icoder.bat and icoder_local.bat launchers`

### Step 5: /exit Alias for /quit
> [Detail](./steps/step_5.md) — Register `/exit` as second command pointing to same handler

- [ ] Implementation: tests (`tests/icoder/test_command_registry.py`) + production code (`src/mcp_coder/icoder/core/commands/quit.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: add /exit alias for /quit`

### Step 6: UI Spacing — Blank Lines Between Conversation Turns
> [Detail](./steps/step_6.md) — Add `write("")` blank lines after user input and after LLM response

- [ ] Implementation: production code (`src/mcp_coder/icoder/ui/app.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: blank line spacing between conversation turns`

### Step 7: UI Color Coding with Rich Text Styles
> [Detail](./steps/step_7.md) — Add optional `style` parameter to `OutputLog` methods, define style constants in `app.py`

- [ ] Implementation: tests (`tests/icoder/test_widgets.py`) + production code (`src/mcp_coder/icoder/ui/widgets/output_log.py`, `src/mcp_coder/icoder/ui/app.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `icoder: Rich color coding for user input, tool output, and LLM text`

## Pull Request
- [ ] PR review: verify all steps complete and checks green
- [ ] PR summary prepared
