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

### Step 1: Install output through logging — [step_1.md](./steps/step_1.md)
- [ ] Implementation: migrate `capsys` → `caplog` in `test_install_phases.py` / `test_install_post_checks.py`, then replace every `print()` in `src/mcp_coder/install/` with `logger.log(OUTPUT, ...)` / `logger.error(...)`
- [ ] Quality checks (ruff, pylint, mypy, pytest fast unit tests) — fix all issues
- [ ] Commit message prepared

### Step 2: Capture helper and retry loop in `_env.py` — [step_2.md](./steps/step_2.md)
- [ ] Implementation: write `tests/install/test_install_retry.py`, then add `Signature`, `UV_TRANSIENT_SIGNATURES`, `_can_capture_stderr`, `_match_signature`, `_drain_stderr`, `_run_capturing` and `run(retry_on=...)`; update `_env.py` module docstring and `.importlinter` comment
- [ ] Quality checks (ruff, pylint, mypy, lint-imports, pytest fast unit tests) — fix all issues
- [ ] Commit message prepared

### Step 3: Retry at the uv install/sync call sites — [step_3.md](./steps/step_3.md)
- [ ] Implementation: add `TestRetryCallSites` to `test_install_phases.py`, then pass `retry_on=UV_TRANSIENT_SIGNATURES` at every `uv pip install` / `uv sync` call in `_phases.py` and `__init__.py`; update `docs/configuration/setup.md` and `docs/cli-reference.md`
- [ ] Quality checks (ruff, pylint, mypy, pytest fast unit tests) — fix all issues
- [ ] Commit message prepared

### Step 4: Classifier retry signatures and PIPE-NO-STATUS suppression — [step_4.md](./steps/step_4.md)
- [ ] Implementation: add tests to `tests/tools/test_jenkins_classify_logs.py`, then add `MC-INSTALL-UV-RETRY` / `MC-INSTALL-UV-RETRY-OK` signatures and `no_status_suppressed_by` to `jenkins_issue_patterns.toml`, honour it in `jenkins_classify_logs.py`; update `tools/jenkins_issue_analysis.md`
- [ ] Quality checks (ruff, pylint, mypy, pytest fast unit tests) — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against `main` and address findings
- [ ] PR summary prepared
