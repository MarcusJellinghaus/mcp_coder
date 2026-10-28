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

### Step 1: Marker definitions and `-m` filters (config, CI, tooling)
See [step_1.md](./steps/step_1.md)

- [x] Implementation: precondition collect-only check (0 tests selected), then remove the three markers from `pyproject.toml`, `ci.yml`, `.claude/CLAUDE.md`, `.run/` config, `get_pytest_performance_stats.bat`, `ci_coverage_summary.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Dead test code and unused GitHub fixtures
See [step_2.md](./steps/step_2.md)

- [x] Implementation: precondition search, then delete commented-out Claude API test code, GitHub fixtures in `tests/conftest.py` with their imports, and vulture whitelist entries
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Docs, plus the final acceptance search
See [step_3.md](./steps/step_3.md)

- [x] Implementation: update `tests/README.md`, `architecture.md`, `runtime_statistics.md`, `runtime-statistics-review-process.md`; acceptance search finds hits only under `docs/tests/performance_data/`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main` and address findings
- [ ] PR summary prepared
