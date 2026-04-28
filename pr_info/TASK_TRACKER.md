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

### Step 1: Add Helpers, Bump `_pad`, Migrate `_format_section`

See [step_1.md](./steps/step_1.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Migrate `_format_mcp_section` and `_format_claude_mcp_section`

See [step_2.md](./steps/step_2.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Migrate `_print_environment_section` and `_print_project_section`

See [step_3.md](./steps/step_3.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Change `_collect_mcp_warnings` Return Type and Migrate `_run_mcp_edit_smoke_test`

See [step_4.md](./steps/step_4.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Migrate `execute_verify` Inline Rows (CONFIG, PROMPTS, LLM PROVIDER, Test prompt)

See [step_5.md](./steps/step_5.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Alignment-Invariant Tests

See [step_6.md](./steps/step_6.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary

