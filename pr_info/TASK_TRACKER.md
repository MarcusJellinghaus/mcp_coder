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

### Step 1: SUPPORTED_PROVIDERS constant + update all consumers
See [step_1.md](./steps/step_1.md)
- [x] Implementation: add `SUPPORTED_PROVIDERS` to `types.py`, update `resolver.py`, `parsers.py`, `utils.py`, `pyproject.toml`, `CLAUDE.md` + tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Shared executable finder utility
See [step_2.md](./steps/step_2.md)
- [ ] Implementation: create `utils/executable_finder.py` with `find_executable()` + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Copilot log paths + shared log utilities
See [step_3.md](./steps/step_3.md)
- [ ] Implementation: extract shared `log_utils.py`, create `copilot_cli_log_paths.py`, update Claude imports + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Copilot JSONL parser + tool permission converter
See [step_4.md](./steps/step_4.md)
- [ ] Implementation: add `parse_copilot_jsonl_line()`, `parse_copilot_jsonl_output()`, `convert_settings_to_copilot_tools()` to `copilot_cli.py` + conftest fixtures + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Copilot command builder + `ask_copilot_cli()`
See [step_5.md](./steps/step_5.md)
- [ ] Implementation: move `logging_utils.py` to `llm/`, add `build_copilot_command()`, `ask_copilot_cli()`, `_read_settings_allow()` + update imports + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Copilot streaming
See [step_6.md](./steps/step_6.md)
- [ ] Implementation: create `copilot_cli_streaming.py` with `ask_copilot_cli_stream()` + event mapping + update `__init__.py` exports + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Interface integration
See [step_7.md](./steps/step_7.md)
- [ ] Implementation: add `"copilot"` branch in `prompt_llm()` and `prompt_llm_stream()`, use `SUPPORTED_PROVIDERS` for validation + tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
