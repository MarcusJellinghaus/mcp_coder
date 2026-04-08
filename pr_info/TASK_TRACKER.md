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

### Step 1: Build-time packaging infrastructure
> [step_1.md](./steps/step_1.md) — `setup.py` with custom `build_py`, `pyproject.toml` package-data, `.gitignore` update

- [x] Implementation: `setup.py`, `pyproject.toml` package-data, `.gitignore`, tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: CLI parser for init command
> [step_2.md](./steps/step_2.md) — `add_init_parser()` with `--just-skills` and `--project-dir` flags

- [x] Implementation: `parsers.py`, `main.py`, `init.py` signature update, tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Runtime skill source resolver
> [step_3.md](./steps/step_3.md) — `_find_claude_source_dir()` with dual-lookup logic

- [x] Implementation: `_find_claude_source_dir()` in `init.py`, tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Deploy logic and integration into execute_init
> [step_4.md](./steps/step_4.md) — `_deploy_skills()` + `execute_init()` integration

- [x] Implementation: `_deploy_skills()`, `execute_init()` update, tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Documentation updates
> [step_5.md](./steps/step_5.md) — Replace hand-copy instructions with `mcp-coder init` references

- [x] Implementation: `docs/repository-setup/claude-code.md`, `docs/repository-setup/README.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [x] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
