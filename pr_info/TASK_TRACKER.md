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

### Step 1: `BuildInfo` and pure build functions (`builds.py`)
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `test_builds.py` (no mocks), `BuildInfo` in `models.py` + export, new `builds.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `JenkinsClient.get_recent_builds` and `get_console_output`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `test_client_builds.py` (python-jenkins mocked), two methods in `client.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move Jenkins integration fixtures to `integration_fixtures.py`
See [step_3.md](./steps/step_3.md)

- [x] Implementation: new `integration_fixtures.py`, fixtures removed from `test_integration.py`, re-exported in `conftest.py`
- [x] Quality checks: pylint, pytest (incl. `jenkins_integration`), mypy, ruff — fix all issues
- [x] Commit message prepared

### Step 4: Integration tests for `get_recent_builds` / `get_console_output`
See [step_4.md](./steps/step_4.md)

- [x] Implementation: three integration tests in `test_integration.py`, module docstring updated
- [x] Quality checks: pylint, pytest (incl. `jenkins_integration`), mypy — fix all issues
- [x] Commit message prepared

### Step 5: `jenkins_builds` tool, wrappers and tests
See [step_5.md](./steps/step_5.md)

- [ ] Implementation: `tests/tools/test_jenkins_builds.py`, `tools/jenkins_builds.py`, `.bat` / `.sh` (staged executable)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `jenkins_download_logs` tool, wrappers and tests
See [step_6.md](./steps/step_6.md)

- [ ] Implementation: `tests/tools/test_jenkins_download_logs.py`, `tests/tools/conftest.py`, `tools/jenkins_download_logs.py`, `.bat` / `.sh` (staged executable)
- [ ] Quality checks: pylint, pytest (incl. `jenkins_integration`), mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Docs and agent setup
See [step_7.md](./steps/step_7.md)

- [ ] Implementation: `docs/repository-setup/internal.md` rows, `## Jenkins` in `.claude/CLAUDE.md`, allow entries in `.claude/settings.local.json`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`
- [ ] PR summary prepared
