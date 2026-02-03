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

### Step 1: Add Environment Variable Setup to VENV_SECTION_WINDOWS
See [step_1.md](./steps/step_1.md)

- [x] Create new test `test_creates_script_with_env_var_setup` in `tests/workflows/vscodeclaude/test_workspace.py`
- [x] Add mismatch warning and env var setup to `VENV_SECTION_WINDOWS` in `src/mcp_coder/workflows/vscodeclaude/templates.py`
- [x] Run pylint on modified files and fix any issues
- [x] Run pytest for Step 1 changes and ensure all tests pass
- [x] Run mypy on modified files and fix any type errors
- [x] Prepare git commit message for Step 1

### Step 2: Remove V2 Suffix from Template Names
See [step_2.md](./steps/step_2.md)

- [x] Rename 4 constants in `src/mcp_coder/workflows/vscodeclaude/templates.py` (remove `_V2` suffix)
- [x] Update 8 references in `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- [x] Run pylint on modified files and fix any issues
- [x] Run pytest for Step 2 changes and ensure all tests pass
- [x] Run mypy on modified files and fix any type errors
- [x] Prepare git commit message for Step 2

### Step 3: Final Verification
See [step_3.md](./steps/step_3.md)

- [x] Run all vscodeclaude workflow tests
- [x] Run full pylint check
- [x] Run full pytest suite
- [x] Run full mypy check
- [x] Verify all acceptance criteria from Decisions.md are met

---

## Pull Request

- [x] Review all commits are properly organized (bug fix separate from rename)
- [x] Create PR title and description summarizing Issue #402 fix
- [x] Ensure PR links to Issue #402
- [x] Final review of all changes
