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

### Step 1: Format `tools/` files before lint fixes
See [step_1.md](./steps/step_1.md)

- [x] Implementation: run formatter on `tools/`, keep only the 8 expected files (or files with ruff findings)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `style(tools): format files touched by ruff fixes`

### Step 2: Ruff config — select `PLW1510`, add `tools/` ignores
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `pyproject.toml` — add `PLW1510` to `select`; per-file ignores `tools/**` DOC201 and `tools/safe_delete_folder.py` S607
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `chore(ruff): select PLW1510, add tools/ ignores`

### Step 3: Fix `F` findings (dead code) in `tools/`
See [step_3.md](./steps/step_3.md)

- [x] Implementation: ruff fix `F` on `tools/`; bare `yield` for F841; remove leftover F401 by hand; format touched files only
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `fix(tools): remove dead code flagged by ruff F`

### Step 4: Fix the remaining ruff findings in `tools/`
See [step_4.md](./steps/step_4.md)

- [x] Implementation: ruff autofix on `tools/`; manual fixes (`check=False`, `noqa: S314`, ANN hooks, `main() -> int`, D, SIM, B007); format touched files only; `ruff check src tests tools` → 0
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `chore(tools): fix remaining ruff findings`

### Step 5: CI — lint `tools/`, rename job to `ruff`; scripts and docs
See [step_5.md](./steps/step_5.md)

- [x] Implementation: `ci.yml` matrix entry → `ruff` with `src tests tools`; `tools/ruff_check.sh/.bat`; `docs/repository-setup/python.md`; no `ruff-docstrings` left
- [x] Quality checks: ruff, pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `ci(ruff): lint tools/, rename job to ruff`

## Pull Request

- [ ] PR review: review full branch diff against `main`
- [ ] PR summary prepared (include: "After merge: if `ruff-docstrings` is a required status check on `main`, update branch protection to require `ruff` instead.")
