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

### Step 1: Generator — pin, permissions, trust gate, separator (TDD)
See [step_1.md](./steps/step_1.md)

- [x] Implementation: tests in `test_define_labels_actions.py` + `_GITHUB_SCRIPT_REF`, `permissions: {}`, `author_association` gate, `\n\n` separator in `define_labels_actions.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Regenerate committed workflows, replace doc snippets, consistency test
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `TestGeneratedWorkflowsConsistency` test, regenerate `approve-command.yml` / `label-new-issues.yml` via scratch probe, replace YAML snippets + re-run note in `github.md` and `label-setup.md`, delete `.scratch/`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Document the label-workflow rule
See [step_3.md](./steps/step_3.md)

- [x] Implementation: "Label-Changing Workflows Must Gate on Author Trust" subsection + Trust and Validation bullet in `docs/repository-setup/github.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: `SECURITY.md` and shared-files table row
See [step_4.md](./steps/step_4.md)

- [x] Implementation: create `SECURITY.md`, add row to `docs/repository-setup/README.md` shared-files table
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: SHA-pin the non-generated workflows
See [step_5.md](./steps/step_5.md)

- [ ] Implementation: pin all `uses:` in `ci.yml`, `upstream-compat-check.yml`, `publish.yml`; self-check all 40 `uses:` lines are pinned
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Signed release assets job
See [step_6.md](./steps/step_6.md)

- [ ] Implementation: add `attach-signed-artifacts` job to `publish.yml`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared (incl. manual follow-ups: task 7 ruleset/branch protection, task 8 SAST re-check, signed-release verification after next release)
