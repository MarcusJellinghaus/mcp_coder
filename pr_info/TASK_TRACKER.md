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

### Step 1: `JenkinsClient.base_url` and `_http` ([step_1.md](./steps/step_1.md))

- [x] Implementation: `TestJenkinsClientHttpAccess` tests + `base_url` / `_http` properties (auth resolved lazily in `_http`), `coordinator/core.py:449-451` uses `base_url`, 15 `Mock()` → `MagicMock()` doubles
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `docs/repository-setup/jenkins.md` ([step_2.md](./steps/step_2.md))

- [x] Implementation: write `jenkins.md` (permission matrix, credentials, verifying, troubleshooting, fail-fast note) + register row in `docs/repository-setup/README.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `jenkins_operations/diagnostics.py` ([step_3.md](./steps/step_3.md))

- [x] Implementation: hostile HTML fixture + `test_diagnostics.py`, then `diagnostics.py` (`job_url_path`, `extract_jenkins_error`, `probe`, `diagnose_403`, `diagnose_404`), widen `.importlinter:334`, `core.py:452-456` uses `job_url_path()`
- [x] Quality checks: pylint, pytest, mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 4: `_wrap_jenkins_error` and handler wiring ([step_4.md](./steps/step_4.md))

- [x] Implementation: ten tests incl. fixture payload swap at `test_client.py:272` and moving the 500 case, then `_clean_jenkins_message` + `_wrap_jenkins_error` + `except JenkinsException` branch (before `except HTTPError`) in `start_job` and `get_job_status`
- [ ] Quality checks: pylint, pytest, mypy, lint-imports — fix all issues
      - **Blocked on a stale `.venv`, not on this branch.** `mcp-workspace` is an
        unpinned git dependency (`pyproject.toml:348`), and the installed copy predates
        `mcp_workspace.checks.branch_status_rendering`. Everything below traces to that
        one gap; no finding touches a file this branch changed.
      - lint-imports: **PASS** (21 contracts kept).
      - pytest: **could not run at all** — `src/mcp_coder/checks/branch_status.py:17`
        raises `ModuleNotFoundError`, so `import mcp_coder` fails during collection for
        every test module, including `test_client.py` and `test_diagnostics.py`. The nine
        new step-4 tests have therefore never executed.
      - mypy: 8 errors, all environment-caused — missing `branch_status_rendering`,
        plus `BranchStatusReport.pr_feedback_undeterminable`, the `fail_on_reviews`
        kwarg on `format_for_*`, and `PullRequestManager.add_assignees`, which all
        exist in current `mcp-workspace` main but not in the installed build.
      - pylint: same 7 errors (E1123/E0611/E1101) from that stale build, plus E0401 for
        the uninstalled optional extras (`langchain*`, `mcp.server.fastmcp`).
      - **Fix:** run `tools\reinstall_local.bat` (it passes `--refresh` and installs the
        langchain extras, clearing the E0401 noise too), then re-run all four checks.
- [x] Commit message prepared

### Step 5: Drop `exc_info=True` at both coordinator sites ([step_5.md](./steps/step_5.md))

- [ ] Implementation: two `record.exc_info is None` tests, then drop `exc_info=True` at `commands.py:160` and `:329` and correct the stale comment
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `verify_jenkins()` and the two verify sections ([step_6.md](./steps/step_6.md))

- [ ] Implementation: autouse `_neutral_jenkins_verify` fixture + `test_verify_jenkins.py`, then `verify_jenkins.py`, `verify.py` wiring after `:385`, `jenkins_ok` on `_compute_exit_code`, three `_LABEL_MAP` entries
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, file-size (750) — fix all issues
- [ ] Commit message prepared

### Step 7: `cli-reference.md` `--dry-run` boy-scout fix ([step_7.md](./steps/step_7.md))

- [ ] Implementation: correct prose and example commands at `docs/cli-reference.md:505-506` and `:1155-1156`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review — address all review comments
- [ ] PR summary prepared
