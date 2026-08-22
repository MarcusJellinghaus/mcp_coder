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

### Step 1: BLOCKED_FILE constant + read_and_clear_blocked() helper

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — re-verified; **pytest still blocked**.
  - pylint: no issues in any file this step touches. All reported errors are
    `E0401`/`E0611` for uninstalled optional deps (`langchain_*`, `httpx`,
    `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the same stale
    `mcp-workspace` described below.
  - mypy: 8 errors, none in this step's files; same two root causes
    (stale `mcp-workspace`, missing optional deps).
  - pytest: **blocked**. `src/mcp_coder/checks/branch_status.py:17` imports
    `mcp_workspace.checks.branch_status_rendering`, which is absent from the
    `mcp-workspace` installed in `.venv`. That import runs via
    `mcp_coder/__init__.py:37`, so every test module importing `mcp_coder`
    fails at collection — `TestReadAndClearBlocked` collects 0 tests.
    `mcp-workspace` is installed unpinned from git main (`pyproject.toml:348`) and the
    upstream repo *does* contain `branch_status_rendering.py`, so the `.venv`
    copy has simply drifted behind main.
  - Remediation (environment change — needs an explicit go-ahead, and is not
    something this step should make on its own):
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
    then re-run the three checks and tick this box.
  - Pre-existing and unrelated to this step: the step is a pure addition and
    touches no file that any check complains about.
- [x] Commit message prepared

### Step 2: TaskOutcome replaces tuple[bool, str]

Details: [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Blocked detection in process_single_task

Details: [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: status-06f-blocked:implementation-blocked label

Details: [step_4.md](./steps/step_4.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: core.py routes blocked + final-mypy cleanup

Details: [step_5.md](./steps/step_5.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: RETRY_REMINDER + prompts.md blocked exit

Details: [step_6.md](./steps/step_6.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: finalisation.py marker cleanup + commit_message_path fix

Details: [step_7.md](./steps/step_7.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Docs — failure-label tables, HTML matrix, architecture note

Details: [step_8.md](./steps/step_8.md)

- [ ] Implementation (docs only)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
