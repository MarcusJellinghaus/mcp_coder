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

### Step 1: Write `quality-and-security-checks.md` — [step_1.md](./steps/step_1.md)

- [ ] Implementation: create `docs/repository-setup/quality-and-security-checks.md` (facts re-verified on main; links and anchors checked by hand)
- [ ] Quality checks: pylint, pytest, mypy, check_file_size — fix all issues
- [ ] Commit message prepared

### Step 2: Link the hub page from the existing docs — [step_2.md](./steps/step_2.md)

- [ ] Implementation: README *Detail Documentation* row + four pointer lines in `python.md` and `github.md` (5 hits for `quality-and-security-checks.md`)
- [ ] Quality checks: pylint, pytest, mypy, check_file_size — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base, address findings
- [ ] PR summary prepared
