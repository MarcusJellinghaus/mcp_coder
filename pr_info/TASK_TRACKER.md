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

### Step 1: `docs/repository-setup/github.md` — Trust and Validation section
See [step_1.md](./steps/step_1.md)

- [x] Implementation: add `### Trust and Validation` subsection; update Parsing Rules, Validation, Epic Branches, Backward Compatibility
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `docs/cli-reference.md` — trust qualifiers
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: qualify `rebase --base-branch`, the `rebase` description and `gh-tool get-base-branch` priority 1
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: User-facing strings and `_resolve_base_branch` docstring
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: trust assertion in `tests/workflows/rebase/test_guards.py` (fails first); qualifier in `rebase.py` error + docstring, `parsers.py` help, `create_pr/core.py` tip, `review/handoff.py` `no_base`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `.claude/skills/issue_update/SKILL.md` — ref-name rule
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: replace the Base Branch single-line sentence with the ref-name rule and fallback behaviour
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`; address findings
- [ ] PR summary prepared
