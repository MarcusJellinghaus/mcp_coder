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

### Step 1: Coordinator `_check_alerts`

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Auto-merge CodeQL wait and alert gate

Details: [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: `pr_comment_triage` skill covers alerts

Details: [step_3.md](./steps/step_3.md)

- [ ] Implementation (skill text only, no new tests)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `status-91` label and PR-health docs

Details: [step_4.md](./steps/step_4.md)

- [ ] Implementation (label test + `labels.json` + docs)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Auto-merge and token docs

Details: [step_5.md](./steps/step_5.md)

- [ ] Implementation (docs only, no new tests)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary: prepare the PR title and description
