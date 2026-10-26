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

### Step 1: `LICENSE` + PEP 639 license metadata — [step_1.md](./steps/step_1.md)

- [x] Implementation: add MIT `LICENSE`; `pyproject.toml` → `setuptools>=77`, `license = "MIT"`, `license-files`, remove `License ::` classifier
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `build: add MIT LICENSE and PEP 639 license metadata`

### Step 2: Coverage badge in `ci.yml` + `README Badges` docs — [step_2.md](./steps/step_2.md)

- [x] Implementation: `coverage` job writes total to step output + `Update coverage badge` step; `## README Badges` section in `docs/repository-setup/github.md`; table rows in `docs/repository-setup/README.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `ci: publish combined coverage badge to gist`

### Step 3: OpenSSF Scorecard workflow — [step_3.md](./steps/step_3.md)

- [x] Implementation: create `.github/workflows/scorecard.yml`; Scorecard/CodeQL docs in `github.md`; shared-files row in `docs/repository-setup/README.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `ci: add OpenSSF Scorecard workflow`

### Step 4: README badge lines — [step_4.md](./steps/step_4.md)

- [x] Implementation: insert three badge lines under `# MCP Coder` in `README.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `docs(readme): add metadata, tooling and security badges`

## Pull Request

- [x] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
