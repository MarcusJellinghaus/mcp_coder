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

### Step 1: Shim `mcp_coder.utils.verify_render`; switch all users; delete local primitives
See [step_1.md](./steps/step_1.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture, deptry) — fix all issues
- [ ] Commit message prepared

### Step 2: GIT / GITHUB / GITHUB SECURITY sections from mcp-workspace; drop PyYAML from runtime deps
See [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture, deptry) — fix all issues
- [ ] Commit message prepared

### Step 3: Remove the pre-f626cf8 `.mcp-file-access` fallback
See [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture, deptry) — fix all issues
- [ ] Commit message prepared

### Step 4: FILE ACCESS section (workspace + reference projects), exit code, docs
See [step_4.md](./steps/step_4.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture, deptry) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
