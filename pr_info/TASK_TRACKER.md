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

### Step 1: Delete unused legacy liveness detection code — [step_1.md](./steps/step_1.md)

- [ ] Implementation: port missing scenarios, delete legacy functions/tests/re-exports, fix comments
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Remove the PID refresh — [step_2.md](./steps/step_2.md)

- [ ] Implementation: test `test_apply_never_changes_vscode_pid`, drop `pid_needs_refresh` / top-level `found_pid` and refresh branch
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Launch grace also covers restarts (`restarted_at`) — [step_3.md](./steps/step_3.md)

- [ ] Implementation: tests + `restarted_at` field, `update_session_pid(restarted_at=)`, age from later timestamp
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Guards against acting on fresh or `NO_WINDOW` inactivity — [step_4.md](./steps/step_4.md)

- [ ] Implementation: tests + `LivenessRule.NO_WINDOW`, `Transition.prior_last_active`, `guard_reason` in `decide` and retry loop, docs
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, tach — fix all issues
- [ ] Commit message prepared

### Step 5: Window title authoritative on Windows after grace — [step_5.md](./steps/step_5.md)

- [ ] Implementation: tests + enum success flag, `window_count` / `title_authoritative` signals, new `assess_liveness` order, DEBUG title dump, docs
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Zombie visibility — [step_6.md](./steps/step_6.md)

- [ ] Implementation: tests + zombie reason naming the signal, `Running (zombie: <rule>)`, restart warning, docs
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Exact title / cmdline matching on name boundaries — [step_7.md](./steps/step_7.md)

- [ ] Implementation: tests + `_contains_bounded`, bounded `_title_binds` and `_cmdline_scan`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Build the workspace file with `json.dumps` — [step_8.md](./steps/step_8.md)

- [ ] Implementation: test + dict/`json.dumps` in `create_workspace_file`, remove `WORKSPACE_FILE_TEMPLATE`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch
- [ ] PR summary prepared
