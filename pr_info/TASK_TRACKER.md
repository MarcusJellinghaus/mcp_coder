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

### Step 1 — Add `verify_config()` Function ([step_1.md](./steps/step_1.md))

- [x] Implementation: tests (`TestVerifyConfig` in `test_user_config.py`) + `verify_config()` in `user_config.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(verify): add verify_config() for config file validation (#552)`

### Step 2 — Integrate CONFIG Section into `verify` Command ([step_2.md](./steps/step_2.md))

- [ ] Implementation: tests (`TestConfigSectionInVerify` + exit code tests in `test_verify_exit_codes.py`) + update `execute_verify()` and `_compute_exit_code()` in `verify.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(verify): integrate CONFIG section into verify command (#552)`

## Pull Request

- [ ] PR review: verify all steps complete, tests pass, no regressions
- [ ] PR summary prepared
