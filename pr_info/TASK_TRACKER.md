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

### Step 1: Move shared `client` fixture and `_FULL_CONFIG` into `tests/tools/conftest.py`
See [step_1.md](./steps/step_1.md)

- [ ] Implementation (tests + production code): move fixture and `_FULL_CONFIG` to conftest, remove copies from `test_jenkins_builds.py` / `test_jenkins_download_logs.py`, update vulture whitelist comment
- [ ] Quality checks (pylint, pytest, mypy, vulture) — fix all issues
- [ ] Commit message prepared

### Step 2: New tool `tools/jenkins_download_log.py` (+ `.sh` / `.bat`), tests and docs
See [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code): `tests/tools/test_jenkins_download_log.py`, `tools/jenkins_download_log.py` / `.sh` / `.bat`, docs and config edits (`internal.md`, `.claude/CLAUDE.md`, `.claude/settings.local.json`, `tools/jenkins_status_check.md`)
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 3: Executable bit on `tools/jenkins_download_log.sh` (human action)
See [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code): write `pr_info/.blocked.txt`; human runs `git add --chmod=+x tools/jenkins_download_log.sh`
- [ ] Quality checks — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against `pr_info/steps/summary.md`
- [ ] PR summary prepared
