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

### Step 1: Command toolkit config model — [step_1.md](./steps/step_1.md)
- [x] Implementation: `mcp_coder.toolkits.command.config` (`parse_config`, `Step`, `Problem`, `ParsedConfig`), packages, `.importlinter` / `tach.toml` entries, tests in `tests/toolkits/command/test_config.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `CommandToolkit.describe` and `run` with the parsers — [step_2.md](./steps/step_2.md)
- [ ] Implementation: `toolkit.py` with `describe`, `run`, exit-code / junit parsers, `fake_npm` fixture in `tests/conftest.py`, tests in `test_toolkit_run.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: `verify`, `prompt_fragments` and registration — [step_3.md](./steps/step_3.md)
- [ ] Implementation: `verify`, `prompt_fragments`, `command` entry point in `pyproject.toml`, `toolkits_isolation` import-linter contracts, tests in `test_toolkit_describe.py` / `test_registration.py`
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, tach, vulture — fix all issues
- [ ] Commit message prepared

### Step 4: Claude provider `bash_grants` + probe integration test — [step_4.md](./steps/step_4.md)
- [ ] Implementation: `bash_grants` through `prompt_llm` / `prompt_llm_stream` to `build_cli_command`, unit tests, `test_bash_grants_integration.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: `llm_permissions` and granted implement / finalisation / CI-fix sessions — [step_5.md](./steps/step_5.md)
- [ ] Implementation: `llm_permissions` / `bash_grants_of` in `toolkit_runner`, grants at implement task, mypy fix, finalisation and `_run_ci_fix`, tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Rebase checks return `fix_text`; binding-level Done-when test — [step_6.md](./steps/step_6.md)
- [ ] Implementation: `_run_all_checks` returns `(keys, fix_texts)`, callers in `rebase.py` updated, `test_command_toolkit_binding.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Rebase toolkit-filled regression prompt and fix-turn grants — [step_7.md](./steps/step_7.md)
- [ ] Implementation: "Rebase Regression Fix" prompt placeholders, `_check_tool_texts`, `_build_regression_fix_prompt`, `_marker_filter_text`, fix-turn `bash_grants`, `rebase_permissions.py` docstring, tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: `mcp-coder verify` gating — [step_8.md](./steps/step_8.md)
- [ ] Implementation: `_toolkit_rows` format gating, `_uses_mcp_tools_py`, Formatter row only for `mcp-tools-py`, tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Docs `docs/configuration/command-toolkit.md` — [step_9.md](./steps/step_9.md)
- [ ] Implementation: write `command-toolkit.md`, link from `docs/README.md`
- [ ] Quality checks: pylint, pytest, mypy, check_file_size — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against base branch
- [ ] PR summary prepared
