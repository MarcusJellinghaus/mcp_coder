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

### Step 1: Move `get_issue_status`, `is_marked`, `lookup_branch` to `workflow_utils/issue_helpers.py` (move only)
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports, vulture, file size) — fix all issues
- [x] Commit message prepared

### Step 2: Move `vscodeclaude/checks.py` to `workflows/pr_health/` with its tests (move only)
See [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports, vulture, file size) — fix all issues
- [x] Commit message prepared

### Step 3: `pr_health` behaviour — new selection, `RepoIdentifier` URL, cache write-back
See [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports, vulture, file size) — fix all issues
- [x] Commit message prepared

### Step 4: Coordinator runs PR-health in `_collect_work`; vscodeclaude stops; delete `get_cached_eligible_issues`
See [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports, vulture, file size) — fix all issues
- [x] Commit message prepared

### Step 5: Multi-status-label ERROR in `_collect_work`
See [step_5.md](./steps/step_5.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, lint-imports, vulture, file size) — fix all issues
- [ ] Commit message prepared

### Step 6: Documentation
See [step_6.md](./steps/step_6.md)

- [ ] Implementation (docs updates)
- [ ] Quality checks (pylint, pytest, mypy, lint-imports, vulture, file size) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch, address findings
- [ ] PR summary prepared (title + description)
