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

### Step 1: Baseline + move `TestSessionIdOutputFormat` → `test_prompt_session_id_format.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: record baseline counts in step_1.md Notes, move `TestSessionIdOutputFormat` with `move_symbol` (dry run first), fix imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move `TestPromptClaudeCwd` → `test_prompt_claude_cwd.py`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: move `TestPromptClaudeCwd` with `move_symbol` (dry run first), import `_make_text_events` from `test_prompt.py`, fix imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move `TestAddSystemPromptsFlag` → `test_prompt_system_prompts.py` + drop allowlist entry
See [step_3.md](./steps/step_3.md)

- [x] Implementation: move `TestAddSystemPromptsFlag` with `move_symbol` (dry run first), fix imports, remove `tests/cli/commands/test_prompt.py` from `.large-files-allowlist`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: compact diff against base branch follows the pure-move rule; counts unchanged (22 tests in the four files, suite total matches baseline)
- [ ] PR summary prepared
