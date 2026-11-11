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

### Step 1: `docs/configuration/toolkits.md` (fold in and delete `command-toolkit.md`)
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: create `toolkits.md`, fold in and delete `command-toolkit.md`, replace the `docs/README.md` entry; run the step's verification searches
- [ ] Quality checks (file size, pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 2: `docs/architecture/toolkit-interface.md` (mcp-coder's side and authoring guide)
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: create `toolkit-interface.md`, add it to `docs/README.md`, link it from the `toolkits.md` intro; run the step's verification searches
- [ ] Quality checks (file size, pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 3: Point the existing docs at the toolkit pages
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: edit the seven existing docs to link the toolkit pages; run the whole-issue "Done when" checks
- [ ] Quality checks (file size, pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `summary.md` "Done when"
- [ ] PR summary prepared (include the plan-vs-code discrepancies from the step commit bodies and the `toolkits.md#npm` anchor note for #1198)
