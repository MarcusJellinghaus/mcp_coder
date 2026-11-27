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

### Step 1: `jenkins_watch.py` — narrow `job` for mypy, pin `--inspect` exit code ([step_1.md](./steps/step_1.md))

- [x] Implementation: test `test_inspect_without_job_exits_2` + `job is None` narrowing in `main()`
- [x] Quality checks (format, ruff, mypy, pylint, pytest) — fix all issues
- [x] Commit message prepared

### Step 2: Remaining mypy `--strict` findings in `tools/` ([step_2.md](./steps/step_2.md))

- [x] Implementation: typing fixes in `generate_report.py`, `test_scroll.py`, mlflow scripts
- [x] Quality checks (format, ruff, mypy on `src tests tools`, pylint, pytest) — fix all issues
- [x] Commit message prepared

### Step 3: pylint findings in `tools/` ([step_3.md](./steps/step_3.md))

- [x] Implementation: targeted disables, unused variables, `encoding="utf-8"`, remove `pass`
- [x] Quality checks (format, ruff, pylint and mypy on `src tests tools`, pytest) — fix all issues
- [x] Commit message prepared

### Step 4: Add `tools` to the mypy / pylint command lines ([step_4.md](./steps/step_4.md))

- [x] Implementation: `ci.yml`, `upstream-compat-check.yml`, `.bat` wrappers, `github.md` template
- [x] Quality checks (search, format, mypy, pylint, pytest) — fix all issues
- [x] Commit message prepared

### Step 5: `script-directories = ["tools"]` in `pyproject.toml` + docs ([step_5.md](./steps/step_5.md))

- [x] Implementation: `pyproject.toml` key, `toolkits.md`, `python.md`, `quality-and-security-checks.md`
- [x] Quality checks (search, format, ruff, mypy, pylint, pytest) — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review all changes on the branch against the plan
- [ ] PR summary prepared
