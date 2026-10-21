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

### Step 1: Wrapper delegates to mcp-tools-py resolution
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Config accessors + single gate in `run_formatters`
See [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Rebase: formatter pre-flight in `_preflight`, fix loop via `run_formatters`
See [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Review pre-flight
See [step_4.md](./steps/step_4.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: fix-ci pre-flight
See [step_5.md](./steps/step_5.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `check_branch_status --fix` pre-flight
See [step_6.md](./steps/step_6.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: verify: `format_code`, Formatter and leftover-key rows; exit code
See [step_7.md](./steps/step_7.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: implement: pre-flight, remove old `format_code` plumbing, remove repo key
See [step_8.md](./steps/step_8.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Text and docs
See [step_9.md](./steps/step_9.md)

- [ ] Implementation (text + docs updates)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`, address findings
- [ ] PR summary prepared
