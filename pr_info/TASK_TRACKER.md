# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Step 1: Update Dependencies and Add Mypy Prompt
- [x] Step 1: Update Dependencies and Add Mypy Prompt - [Details](steps/step_1.md)
  - [x] Move mcp-code-checker from dev dependencies to main dependencies in pyproject.toml
  - [x] Add "Mypy Fix Prompt" section to src/mcp_coder/prompts/prompts.md
  - [x] Quality checks: Run pylint, pytest, mypy
  - [ ] Git commit preparation and commit

### Step 2: Complete Mypy Integration
- [ ] Step 2: Complete Mypy Integration - [Details](steps/step_2.md)
  - [ ] Implement check_and_fix_mypy() function in workflows/implement.py
  - [ ] Integrate mypy checking into process_single_task() workflow
  - [ ] Add smart retry logic (max 3 identical feedback attempts)
  - [ ] Quality checks: Run pylint, pytest, mypy
  - [ ] Git commit preparation and commit

### Pull Request
- [ ] Run detailed quality checks (pylint warnings, pytest runtime)
- [ ] Generate and review PR summary using tools/pr_review.bat
- [ ] Create comprehensive feature summary with tools/pr_summary.bat
- [ ] Clean up PR_Info folder (remove steps/ directory)
- [ ] Push changes and create pull request
