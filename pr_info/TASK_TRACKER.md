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

### Step 1: Split CI by event and document it — [step_1.md](./steps/step_1.md)

- [ ] Implementation: `ci.yml` (`test` → `push-checks`, `architecture` → `pr-checks`, `if:` conditions, comments), `quality-and-security-checks.md` (`## CI events`, Architecture/Dependencies wording), `github.md` CI template
- [ ] Quality checks: pylint, pytest, mypy — fix all issues (plus `check_file_size` and the `architecture|\btest:` search in `ci.yml`)
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`
- [ ] PR summary prepared
