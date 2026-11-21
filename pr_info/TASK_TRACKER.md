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

### Step 1: `get_pr_diff` helper, used by `refresh_pr_description`
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: tests (`TestGetPrDiff`, fixture patches `get_pr_diff`) + `get_pr_diff` in `pr_description.py`, `refresh_pr_description` switched to it
- [ ] Quality checks (format, pylint, mypy, pytest unit, lint-imports) — fix all issues
- [ ] Commit message prepared

### Step 2: `generate_pr_summary` uses `get_pr_diff`
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: `test_generation.py` patches `get_pr_diff`, git-diff-exception test removed + `core.py` call site switched, `get_branch_diff` import dropped
- [ ] Quality checks (format, pylint, mypy, pytest unit + `git_integration`, lint-imports, file size) — fix all issues
- [ ] Commit message prepared

### Step 3: Prompts explain the move markers
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: `test_pr_prompts_explain_moved_markers` + marker sentence in both PR prompts, "full git diff" → "branch diff"
- [ ] Quality checks (format, pylint, mypy, pytest unit) — fix all issues
- [ ] Commit message prepared

### Step 4: Docs and stale comment
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: `08-pr-creation.md`, `cli-reference.md`, `finalisation.py` comment
- [ ] Quality checks (format, pylint, mypy, pytest unit, "full branch diff|full git diff" search) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`, address findings
- [ ] PR summary prepared
