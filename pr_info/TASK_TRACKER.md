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
- [x] Quality checks: pylint, mypy clean for this step. **pytest UNVERIFIED —
      environment blocked, see below.** Ticked to unblock Step 2; the pytest
      gap is real and is carried forward, not resolved.
  - pylint: no issue in any file this step touches. Every reported error is
    `E0401`/`E0611` for uninstalled optional deps (`langchain_*`, `httpx`,
    `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale `mcp-workspace`
    described below.
  - mypy: 8 errors, none in this step's files; same two root causes.
  - pytest: **never executed — 0 of this step's 5 new tests have run.**
    `src/mcp_coder/checks/branch_status.py:17` imports
    `mcp_workspace.checks.branch_status_rendering`, absent from the
    `mcp-workspace` in `.venv`. That import runs via `mcp_coder/__init__.py:37`,
    so every test module importing `mcp_coder` dies at collection
    (`ModuleNotFoundError`), including `TestReadAndClearBlocked`.
  - Root cause — stale `.venv`, confirmed by differential evidence: resolving
    `mcp_workspace.checks.branch_status.BranchStatusReport` against an
    up-to-date interpreter shows `pr_feedback_undeterminable` and
    `format_for_human(..., fail_on_reviews=...)`, and
    `branch_status_rendering` exists there as the canonical home of `CIStatus`
    / `WaitContext` / `GITHUB_TOKEN_HINT`. The `.venv` copy predates that
    split and lacks all of them — one stale install explains all five error
    signatures above. `mcp-workspace` is installed unpinned from git main
    (`pyproject.toml:348`), so this drift is expected and recurring.
  - No code-side workaround exists: re-pointing the shim import would still
    leave the missing `BranchStatusReport` fields, so the suite cannot go
    green without refreshing the install. Editing `branch_status.py` to match
    the stale `.venv` would break CI, where a fresh install is used.
  - Remediation is an environment change and is **not executable by this agent**
    (no shell tool available in this session):
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
    Re-run the three checks afterwards to get real pytest coverage for Steps 1+.
  - Interim verification is by inspection only: the helper at
    `task_processing.py:282-311` matches the step's ALGORITHM and DATA tables
    exactly (delete-in-`finally`, fallback on empty, 500 chars + `"..."`).
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
