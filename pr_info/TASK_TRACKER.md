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

### Step 1: Config reader `get_post_install_checks` + tests
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `TestGetPostInstallChecks` tests + `get_post_install_checks` in `utils/pyproject_config.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `InstallConfig.post_install_checks` read strictly in `from_args` + tests
See [step_2.md](./steps/step_2.md)

- [x] Implementation: `TestPostInstallChecksResolution` tests + new `InstallConfig` field read in `from_args`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `validate_target_repo` validates `post_install_checks` + tests
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: warning tests in `test_validate_target_repo.py` + strict read in `validate_target_repo`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `phase_post_install_checks` + wiring in `install()` + tests
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: `tests/install/test_install_post_checks.py` + `_resolve_check_executable`, `phase_post_install_checks`, wiring in `install()`
- [ ] Quality checks: pylint, pytest, mypy (plus lint-imports, tach) — fix all issues
- [ ] Commit message prepared

### Step 5: Declare this repo's post-install checks in `pyproject.toml`
See [step_5.md](./steps/step_5.md)

- [ ] Implementation: add `post_install_checks` to `[tool.mcp-coder.install]`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Documentation
See [step_6.md](./steps/step_6.md)

- [ ] Implementation: update `config.md`, `cli-reference.md`, `repository-setup/README.md`, `repository-setup/python.md`, `architecture.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against the base branch
- [ ] PR summary prepared
