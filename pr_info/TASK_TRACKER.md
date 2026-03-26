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

### Step 1: Stream Event Types and ResponseAssembler
- [x] Implementation: `StreamEvent` type alias + `ResponseAssembler` class in `types.py` with tests in `test_types.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(types): add StreamEvent type and ResponseAssembler`

### Step 2: stream_subprocess() in subprocess_runner
- [x] Implementation: `stream_subprocess()` generator + `StreamResult` wrapper in `subprocess_runner.py` with tests in `test_subprocess_runner.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(subprocess): add stream_subprocess generator`

### Step 3: Claude CLI Streaming Provider
- [x] Implementation: `ask_claude_code_cli_stream()` in `claude_code_cli.py` with tests in `test_claude_code_cli.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(claude): add ask_claude_code_cli_stream`

### Step 4: LangChain Streaming Provider
- [x] Implementation: `ask_langchain_stream()` + `_ask_text_stream()` in `langchain/__init__.py` with tests in `test_langchain_provider.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(langchain): add ask_langchain_stream`

### Step 5: prompt_llm_stream() Interface + Stream Print Formatting
- [ ] Implementation: `prompt_llm_stream()` in `interface.py` + `print_stream_event()` in `formatters.py` with tests in `test_interface.py` and `test_formatters.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(interface): add prompt_llm_stream and stream formatting`

### Step 6: CLI Changes — New Output Formats, Remove --verbosity, Wire Streaming
- [ ] Implementation: Update `parsers.py` + `prompt.py` for streaming path, remove `--verbosity`, add `ndjson`/`json-raw` formats, with tests in `test_prompt.py` and new `test_prompt_streaming.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(cli): add streaming output formats, remove --verbosity`

## Pull Request
- [ ] PR review: verify all steps integrated, no regressions
- [ ] PR summary prepared
