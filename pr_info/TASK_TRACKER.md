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

### Step 1: Shim — re-export `create_empty_issue_data` ([step_1.md](./steps/step_1.md))
- [x] Implementation: smoke tests (`__all__` count 32, importability test) + re-export in `mcp_workspace_github.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Test factory `make_issue_data` ([step_2.md](./steps/step_2.md))
- [x] Implementation: `tests/test_github_factories.py` (2 tests) + `tests/github_factories.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `prerequisites.py` uses `create_empty_issue_data()` ([step_3.md](./steps/step_3.md))
- [x] Implementation: sentinel assertion in `test_prerequisites.py` + replace `IssueData(...)` literal in `prerequisites.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Migrate `tests/cli/commands` (6 files) ([step_4.md](./steps/step_4.md))
- [ ] Implementation: replace issue literals with `make_issue_data(...)` / `create_empty_issue_data()`; no `locked` matches remain
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Migrate `tests/cli/commands/coordinator` (4 files) ([step_5.md](./steps/step_5.md))
- [ ] Implementation: inline literals and helpers/fixtures → `make_issue_data(...)`; retype receivers; no `locked` matches remain
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Migrate `tests/workflows/create_plan` (6 files) ([step_6.md](./steps/step_6.md))
- [ ] Implementation: fixtures/literals → `make_issue_data(...)`, empty sentinels → `create_empty_issue_data()`; no `locked` matches remain
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Migrate `tests/workflows/vscodeclaude/test_session_restart*` (4 files) ([step_7.md](./steps/step_7.md))
- [ ] Implementation: issue literals → `make_issue_data(...)`; retype receivers; no `locked` matches remain
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Migrate remaining `tests/workflows/vscodeclaude` (14 files) ([step_8.md](./steps/step_8.md))
- [ ] Implementation: inline literals and helpers/fixtures → `make_issue_data(...)`; retype receivers; no `locked` matches remain
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Migrate misc (2 files) + acceptance checks ([step_9.md](./steps/step_9.md))
- [ ] Implementation: `test_branch_info.py` and `test_base_branch.py` → `make_issue_data(...)`; acceptance searches clean, lint-imports passes
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
