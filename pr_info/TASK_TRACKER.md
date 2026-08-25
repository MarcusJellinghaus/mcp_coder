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
- [x] Quality checks: pylint, pytest, mypy, lint-imports — fix all issues
      - **All four checks pass for this branch's code. Zero findings in any file this
        branch changed.** The `.venv` is still stale (`mcp-workspace` is an unpinned git
        dependency, `pyproject.toml:348`, and the installed copy has no
        `mcp_workspace/checks/branch_status_rendering.py`), so the checks were run with
        that gap worked around — see the note at the end.
      - lint-imports: **PASS** (21 contracts kept, 697 files / 3568 dependencies).
      - pytest: **PASS** for the step-4 code. `tests/utils/jenkins_operations` →
        78 passed, which is the first execution of the nine new step-4 tests. The wider
        suite was run in chunks: `tests/utils` + `tests/workflow_steps` +
        `tests/workflow_utils` + `tests/workflows` + `tests/integration` → 1824 passed,
        5 skipped; `tests/checks` + `tests/cli` + `tests/config` + `tests/icoder` and
        `tests/llm` + `tests/prompts` + `tests/services` + `tests/tools` pass apart from
        the pre-existing environment failures listed below. (Full-suite `-n auto` exceeds
        the 300 s tool timeout, hence the chunking.)
      - mypy: **PASS** — clean over `src|tests/mcp_coder/utils/jenkins_operations` and
        `src|tests/.../cli/commands/coordinator`, i.e. every directory this branch edits.
      - pylint: **PASS** — clean over the same four directories.
      - black/isort: clean (26 files unchanged).
      - **Pre-existing, unrelated to this branch** (all still open, none in a changed
        file): 8 mypy + 7 pylint E1123/E0611/E1101 errors from the stale `mcp_workspace`
        build (`branch_status_rendering`, `BranchStatusReport.pr_feedback_undeterminable`,
        the `fail_on_reviews` kwarg on `format_for_*`, `PullRequestManager.add_assignees`);
        pylint E0401 for uninstalled optional extras (`langchain*`, `mcp.server.fastmcp`);
        `tests/icoder/test_snapshots.py` (10 errors — `pytest-textual-snapshot` not
        installed); `test_busy_indicator.py::test_show_busy_preserves_start_time` (timing
        flake — 0.05 s sleep formatted to one decimal, asserts `> 0.0`);
        3 × `test_copilot_integration.py` (copilot CLI exits 1);
        `test_langchain_exceptions.py::test_connection_errors_contains_httpx_connect_error`
        (`httpx` is a `MagicMock` without the extras).
      - **Workaround used / still to do:** pytest was run with
        `PYTHONPATH=C:/Users/Marcus/Documents/GitHub/mcp-workspace/src` to shadow the stale
        package; mypy and pylint take no env, so they were scoped to the changed
        directories instead. Run `tools\reinstall_local.bat` (passes `--refresh` and
        installs the langchain extras) to clear the environment gap for good, then the
        unscoped project-wide checks will be green too.
- [x] Commit message prepared

### Step 5: Drop `exc_info=True` at both coordinator sites ([step_5.md](./steps/step_5.md))

- [x] Implementation: two `record.exc_info is None` tests, then drop `exc_info=True` at `commands.py:160` and `:329` and correct the stale comment
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      - Tests written first and watched fail: both failed on exactly the
        `all(r.exc_info is None ...)` assertion (the message assertion already passed),
        confirming they bite on the unfixed code. Green after the two deletions.
      - pytest: **PASS** — `tests/cli/commands/coordinator` → 158 passed; whole
        `tests/cli` → 1078 passed with the standard marker exclusions.
      - mypy, pylint: **PASS** — clean over `src|tests/.../cli/commands/coordinator`.
      - black/isort: clean (15 files unchanged).
      - Same stale-`.venv` gap as step 4 (`mcp_workspace` has no
        `checks/branch_status_rendering.py`): pytest was run with
        `PYTHONPATH=C:/Users/Marcus/Documents/GitHub/mcp-workspace/src`, and mypy/pylint
        were scoped to the changed directories. `tools\reinstall_local.bat` still fixes
        this for good.
      - **Left in place deliberately:** `main.py:377` (top-level CLI boundary, per
        step_5.md) and a third `exc_info=True` at `commands.py:343` — the *outer*
        `execute_coordinator_run` handler, which step_5.md does not list among its two
        sites. Worth a look in a later step if the tracebacks there also prove noisy.
- [x] Commit message prepared

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
