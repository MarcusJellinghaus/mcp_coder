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

### Step 1: Add `from_github` to data layer (types + helpers)
See [step_1.md](./steps/step_1.md)
- [x] Implementation: Add `from_github: bool` to `VSCodeClaudeSession` TypedDict, update `build_session()`, update all session dict literals in src/ and tests/ (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add always-run editable install to VENV_SECTION_WINDOWS
See [step_2.md](./steps/step_2.md)
- [x] Implementation: Append `uv pip install -e . --no-deps` to `VENV_SECTION_WINDOWS` in templates.py (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Core logic — pyproject.toml reading + github install generation
See [step_3.md](./steps/step_3.md)
- [x] Implementation: Add `from_github` param to `create_startup_script()`, read `[tool.mcp-coder.from-github]` from pyproject.toml, generate `uv pip install` commands in .bat script (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Thread `from_github` through session_launch.py
See [step_4.md](./steps/step_4.md)
- [x] Implementation: Add `from_github` param to `process_eligible_issues()`, `prepare_and_launch_session()`, `regenerate_session_files()` and thread to `create_startup_script()` + `build_session()` (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: CLI flag + command wiring
See [step_5.md](./steps/step_5.md)
- [x] Implementation: Add `--from-github` argument to vscodeclaude launch subparser, wire `args.from_github` through `execute_coordinator_vscodeclaude()` and `_handle_intervention_mode()` (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Add `[tool.mcp-coder.from-github]` to pyproject.toml
See [step_6.md](./steps/step_6.md)
- [x] Implementation: Add `[tool.mcp-coder.from-github]` config section to pyproject.toml with package specs, add TOML parse test (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
