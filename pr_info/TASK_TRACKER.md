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

### Step 1: CI polling — read `lookup_failed` from the top level of `CIStatusData`
See [step_1.md](./steps/step_1.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: CI polling — cap the "no run" wait when `expected_sha` is given
See [step_2.md](./steps/step_2.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move `_poll_mergeable_state` to `workflow_steps/rebase.py`
See [step_3.md](./steps/step_3.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: `labels.json` — `status-09:pr-creating` stale timeout 30 min
See [step_4.md](./steps/step_4.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: `ci.yml` — run `pull_request` for PRs against any base
See [step_5.md](./steps/step_5.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: PR summary diff excludes all of `pr_info/`
See [step_6.md](./steps/step_6.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 7: create-pr — rebase before the summary when the branch is behind
See [step_7.md](./steps/step_7.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 8: Refactor create-pr — extract `_cleanup_commit_push` and `_resolve_issue_from_pr`
See [step_8.md](./steps/step_8.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 9: Phase B module `create_pr/post_creation.py`
See [step_9.md](./steps/step_9.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 10: Wire phase B into create-pr (two guards, final label, exit 0)
See [step_10.md](./steps/step_10.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 11: Resume path — an open PR for the branch skips phase A
See [step_11.md](./steps/step_11.md)
- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 12: Docs
See [step_12.md](./steps/step_12.md)
- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 13: Move PR text helpers to `workflow_steps/pr_description.py` (blocked by mcp-workspace#349)
See [step_13.md](./steps/step_13.md)
- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 14: `refresh_pr_description` + prompt (blocked by mcp-workspace#349)
See [step_14.md](./steps/step_14.md)
- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 15: Call the refresh from create-pr phase B and `fix-ci` (blocked by mcp-workspace#349)
See [step_15.md](./steps/step_15.md)
- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review all changes against the summary and steps
- [ ] PR summary prepared
